# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Backend plugin to manage multiple code completion and introspection clients.
"""

# Standard library imports
import logging
import os
import os.path as osp
import functools

# Third-party imports
from qtpy.QtCore import QObject, Slot, QMutex, QMutexLocker

# Local imports
from spyder.config.base import get_conf_path, running_under_pytest
from spyder.config.lsp import PYTHON_CONFIG
from spyder.api.completion import SpyderCompletionPlugin
from spyder.utils.misc import select_port, getcwd_or_home
from spyder.plugins.completion.languageserver.plugin import (
    LanguageServerPlugin)
from spyder.plugins.completion.kite.plugin import KiteCompletionPlugin
from spyder.plugins.completion.fallback.plugin import FallbackPlugin
from spyder.plugins.completion.languageserver import LSPRequestTypes


logger = logging.getLogger(__name__)


class CompletionManager(SpyderCompletionPlugin):
    CONF_SECTION = 'completions'
    CONF_FILE = False

    STOPPED = 'stopped'
    RUNNING = 'running'
    BASE_PLUGINS = {p.COMPLETION_CLIENT_NAME: p for p in (
        LanguageServerPlugin,
        FallbackPlugin,
        KiteCompletionPlugin,
    )}

    GOOD_COMPLETIONS_SOURCES = {
        KiteCompletionPlugin.COMPLETION_CLIENT_NAME,
        LanguageServerPlugin.COMPLETION_CLIENT_NAME,
    }

    MUTEX_REQUEST_TYPES = {
        LSPRequestTypes.DOCUMENT_COMPLETION,
        LSPRequestTypes.DOCUMENT_HOVER,
        LSPRequestTypes.DOCUMENT_SIGNATURE,
    }

    COMPLETION_SOURCE_PRIORITY = (
        KiteCompletionPlugin.COMPLETION_CLIENT_NAME,
        LanguageServerPlugin.COMPLETION_CLIENT_NAME,
        FallbackPlugin.COMPLETION_CLIENT_NAME,
    )

    def __init__(self, parent, plugins=['lsp', 'kite', 'fallback']):
        SpyderCompletionPlugin.__init__(self, parent)
        self.clients = {}
        self.requests = {}
        self.language_status = {}
        self.started = False
        self.first_completion = False
        self.req_id = 0
        self.completion_first_time = 500
        self.waiting_time = 1000
        self.collection_mutex = QMutex()

        self.plugin_priority = {
            LSPRequestTypes.DOCUMENT_COMPLETION: 'lsp',
            LSPRequestTypes.DOCUMENT_SIGNATURE: 'lsp',
            LSPRequestTypes.DOCUMENT_HOVER: 'lsp',
            'all': 'lsp'
        }

        self.response_priority = [
            'lsp', 'kite', 'fallback'
        ]

        for plugin in plugins:
            if plugin in self.BASE_PLUGINS:
                Plugin = self.BASE_PLUGINS[plugin]
                plugin_client = Plugin(self.main)
                self.register_completion_plugin(plugin_client)

    def register_completion_plugin(self, plugin):
        logger.debug("Completion plugin: Registering {0}".format(
            plugin.COMPLETION_CLIENT_NAME))
        plugin_name = plugin.COMPLETION_CLIENT_NAME
        self.clients[plugin_name] = {
            'plugin': plugin,
            'status': self.STOPPED
        }
        plugin.sig_response_ready.connect(self.receive_response)
        plugin.sig_plugin_ready.connect(self.client_available)
        for language in self.language_status:
            server_status = self.language_status[language]
            server_status[plugin_name] = False

    @Slot(str, int, dict)
    def receive_response(self, completion_source, req_id, resp):
        logger.debug("Completion plugin: Request {0} Got response "
                     "from {1}".format(req_id, completion_source))

        if req_id not in self.requests:
            return
        request_responses = self.requests[req_id]
        request_responses['sources'][completion_source] = resp

        if (request_responses['req_type'] ==
                LSPRequestTypes.DOCUMENT_COMPLETION and
                (completion_source not in self.GOOD_COMPLETIONS_SOURCES or
                 not resp)):
            # Check if there's any work remaining that may return completions,
            # since we don't have "good" completions from the current response
            if any(source in self.clients and
                   source not in request_responses['sources']
                   for source in self.GOOD_COMPLETIONS_SOURCES):
                return
        else:
            del self.requests[req_id]

        with QMutexLocker(self.collection_mutex):
            self.gather_and_send(request_responses)

    @Slot(str)
    def client_available(self, client_name):
        client_info = self.clients[client_name]
        client_info['status'] = self.RUNNING

    def gather_completions(self, req_id_responses):
        merge_stats = {source: 0 for source in req_id_responses}
        responses = []
        dedupe_set = set()
        for priority, source in enumerate(self.COMPLETION_SOURCE_PRIORITY):
            if source not in req_id_responses:
                continue
            for response in req_id_responses[source].get('params', []):
                dedupe_key = response['label'].strip()
                if dedupe_key in dedupe_set:
                    continue
                dedupe_set.add(dedupe_key)

                response['sortText'] = '{} {}'.format(
                    priority, response['sortText'])
                responses.append(response)
                merge_stats[source] += 1

        logger.debug('Responses statistics: {0}'.format(merge_stats))
        responses = {'params': responses}
        return responses

    def gather_default(self, responses, default=''):
        response = ''
        for source in self.response_priority:
            response = responses.get(source, {'params': default})
            response = response['params']
            if response is not None and len(response) > 0:
                break
        return {'params': response}

    def gather_and_send(self, request_responses):
        req_type = request_responses['req_type']
        req_id_responses = request_responses['sources']
        response_instance = request_responses['response_instance']
        logger.debug('Gather responses for {0}'.format(req_type))

        if req_type == LSPRequestTypes.DOCUMENT_COMPLETION:
            responses = self.gather_completions(req_id_responses)
        elif req_type == LSPRequestTypes.DOCUMENT_HOVER:
            responses = self.gather_default(req_id_responses, '')
        elif req_type == LSPRequestTypes.DOCUMENT_SIGNATURE:
            responses = self.gather_default(req_id_responses, None)
        else:
            principal_source = self.plugin_priority['all']
            responses = req_id_responses[principal_source]

        try:
            response_instance.handle_response(req_type, responses)
        except RuntimeError:
            # This is triggered when a codeeditor instance has been
            # removed before the response can be processed.
            pass

    def _is_client_running(self, name):
        status = self.clients.get(name, {}).get('status', self.STOPPED)
        return status == self.RUNNING

    def send_request(self, language, req_type, req):
        req_id = self.req_id
        self.req_id += 1

        for client_name in self.clients:
            client_info = self.clients[client_name]
            self.requests[req_id] = {
                'language': language,
                'req_type': req_type,
                'response_instance': req['response_instance'],
                'sources': {},
            }
            client_info['plugin'].send_request(
                language, req_type, req, req_id)

    def send_notification(self, language, notification_type, notification):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].send_notification(
                    language, notification_type, notification)

    def broadcast_notification(self, req_type, req):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].broadcast_notification(
                    req_type, req)

    def project_path_update(self, project_path, update_kind='addition'):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].project_path_update(
                    project_path, update_kind
                )

    def register_file(self, language, filename, codeeditor):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].register_file(
                    language, filename, codeeditor
                )

    def update_configuration(self):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].update_configuration()

    def start(self):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.STOPPED:
                client_info['plugin'].start()

    def shutdown(self):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].shutdown()

    def start_client(self, language):
        started = False
        language_clients = self.language_status.get(language, {})
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_started = client_info['plugin'].start_client(language)
                started |= client_started
                language_clients[client_name] = client_started
        self.language_status[language] = language_clients
        return started

    def stop_client(self, language):
        for client_name in self.clients:
            client_info = self.clients[client_name]
            if client_info['status'] == self.RUNNING:
                client_info['plugin'].stop_client(language)
        self.language_status.pop(language)

    def get_client(self, name):
        return self.clients[name]['plugin']
