# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Main container for the Code completion plugin.
"""

# Standard library imports
import logging
from collections import defaultdict, OrderedDict

# Third-party imports
from qtpy.QtCore import QMutex, QMutexLocker, QTimer, Signal, Slot

# Local imports
from spyder.api.exceptions import SpyderAPIError
from spyder.api.widgets import PluginMainContainer
from spyder.plugins.completion.manager.api import LSPRequestTypes


logger = logging.getLogger(__name__)


class CompletionManagerContainer(PluginMainContainer):

    STOPPED = 'stopped'
    RUNNING = 'running'

    DEFAULT_OPTIONS = {
        "skip_intermediate_requests": {LSPRequestTypes.DOCUMENT_COMPLETION},
        "source_priority": {},
        "completions_wait_for_ms": 300,
        "wait_for_source": {},
    }

    WAIT_FOR_SOURCE = defaultdict(
        lambda: {"lsp"},
        {
            LSPRequestTypes.DOCUMENT_COMPLETION: {
                'kite',
                'lsp',
            },
            LSPRequestTypes.DOCUMENT_SIGNATURE: {
                'kite',
                'lsp',
            },
            LSPRequestTypes.DOCUMENT_HOVER: {
                'kite',
                'lsp',
            },
        })

    SOURCE_PRIORITY = defaultdict(
        lambda: (
            'lsp',
            'kite',
            'fallback',
        ), {
            LSPRequestTypes.DOCUMENT_COMPLETION: (
                'kite',
                'lsp',
                'fallback',
            ),
        })

    SKIP_INTERMEDIATE_REQUESTS = {
        LSPRequestTypes.DOCUMENT_COMPLETION
    }

    def __init__(self, name, plugin, parent=None, options=DEFAULT_OPTIONS):
        super().__init__(name, plugin, parent=parent, options=options)

        self.providers = OrderedDict()
        self.requests = {}
        self.language_status = {}
        self.started = False
        self.req_id = 0
        self.collection_mutex = QMutex(QMutex.Recursive)

        # FIXME: Hardcoding for tests
        self.wait_for_ms = 300

    # --- PluginMainContainer API
    # ------------------------------------------------------------------------
    def setup(self, options=DEFAULT_OPTIONS):
        pass

    def update_actions(self):
        pass

    def on_option_update(self, option, value):
        pass

    # --- Public API
    # ------------------------------------------------------------------------
    def register_completion_provider(self, provider):
        provider_id = provider.ID
        logger.debug("Completion provider: Registering '{0}'".format(provider_id))

        # FIXME: Change name to provider instead of plugin
        self.providers[provider_id] = {
            "provider": provider,
            'status': self.STOPPED
        }

        print(self.providers)

        # Signals
        provider.sig_response_ready.connect(self.receive_response)
        provider.sig_provider_ready.connect(self.client_available)

        for language in self.language_status:
            server_status = self.language_status[language]
            server_status[provider_id] = False

    @Slot(str, int, dict)
    def receive_response(self, completion_source, req_id, resp):
        logger.debug("Completion plugin: Request {0} Got response "
                     "from {1}".format(req_id, completion_source))

        if req_id not in self.requests:
            return

        with QMutexLocker(self.collection_mutex):
            request_responses = self.requests[req_id]
            request_responses['sources'][completion_source] = resp
            self.howto_send_to_codeeditor(req_id)

    @Slot(int)
    def receive_timeout(self, req_id):
        # On timeout, collect all completions and return to the user
        if req_id not in self.requests:
            return

        logger.debug("Completion plugin: Request {} timed out".format(req_id))

        with QMutexLocker(self.collection_mutex):
            request_responses = self.requests[req_id]
            request_responses['timed_out'] = True
            self.howto_send_to_codeeditor(req_id)

    def howto_send_to_codeeditor(self, req_id):
        """
        Decide how to send the responses corresponding to req_id to
        the CodeEditor instance that requested them.
        """
        if req_id not in self.requests:
            return

        request_responses = self.requests[req_id]
        language = request_responses['language']

        # FIXME: Espagueti
        # Skip the waiting logic below when fallback is the only
        # client that works for language
        if self.is_fallback_only(language):
            # Only send response when fallback is among its sources
            if 'fallback' in request_responses['sources']:
                self.gather_and_send_to_codeeditor(request_responses)
                return

            # This drops responses that don't contain fallback
            return

        # Wait between the LSP and Kite to return responses. This favors
        # Kite when the LSP takes too much time to respond.
        wait_for = set(source for source
                       in self.WAIT_FOR_SOURCE[request_responses['req_type']]
                       if self.is_client_running(source))
        timed_out = request_responses['timed_out']
        all_returned = all(source in request_responses['sources']
                           for source in wait_for)

        if not timed_out:
            # Before the timeout
            if all_returned:
                self.skip_and_send_to_codeeditor(req_id)
        else:
            # After the timeout
            any_nonempty = any(request_responses['sources'].get(source)
                               for source in wait_for)
            if all_returned or any_nonempty:
                self.skip_and_send_to_codeeditor(req_id)

    def skip_and_send_to_codeeditor(self, req_id):
        """
        Skip intermediate responses coming from the same CodeEditor
        instance for some types of requests, and send the last one to
        it.
        """
        request_responses = self.requests[req_id]
        req_type = request_responses['req_type']
        response_instance = id(request_responses['response_instance'])
        do_send = True

        # This is necessary to prevent sending completions for old requests
        # See spyder-ide/spyder#10798
        if req_type in self.SKIP_INTERMEDIATE_REQUESTS:
            max_req_id = max(
                [key for key, item in self.requests.items()
                 if item['req_type'] == req_type
                 and id(item['response_instance']) == response_instance]
                or [-1])
            do_send = (req_id == max_req_id)

        logger.debug("Completion plugin: Request {} removed".format(req_id))
        del self.requests[req_id]

        # Send only recent responses
        if do_send:
            self.gather_and_send_to_codeeditor(request_responses)

    def is_fallback_only(self, language):
        """
        Detect if fallback is the only client that works for language.
        """
        lang_status = self.language_status.get(language, {})
        if lang_status:
            if (not lang_status.get('lsp', {}) and
                    not lang_status.get('kite', {})):
                return True

        return False

    def gather_completions(self, req_id_responses):
        """Gather completion responses from plugins."""
        priorities = self.SOURCE_PRIORITY[LSPRequestTypes.DOCUMENT_COMPLETION]

        merge_stats = {source: 0 for source in req_id_responses}
        responses = []
        dedupe_set = set()
        for priority, source in enumerate(priorities):
            if source not in req_id_responses:
                continue
            for response in req_id_responses[source].get('params', []):
                dedupe_key = response['label'].strip()
                if dedupe_key in dedupe_set:
                    continue
                dedupe_set.add(dedupe_key)

                response['sortText'] = (priority, response['sortText'])
                responses.append(response)
                merge_stats[source] += 1

        logger.debug('Responses statistics: {0}'.format(merge_stats))
        responses = {'params': responses}
        return responses

    def gather_responses(self, req_type, responses):
        """Gather responses other than completions from plugins."""
        response = None
        for source in self.SOURCE_PRIORITY[req_type]:
            if source in responses:
                response = responses[source].get('params', None)
                if response:
                    break
        return {'params': response}

    def gather_and_send_to_codeeditor(self, request_responses):
        """
        Gather request responses from all plugins and send them to the
        CodeEditor instance that requested them.
        """
        req_type = request_responses['req_type']
        req_id_responses = request_responses['sources']
        response_instance = request_responses['response_instance']
        logger.debug('Gather responses for {0}'.format(req_type))

        if req_type == LSPRequestTypes.DOCUMENT_COMPLETION:
            responses = self.gather_completions(req_id_responses)
        else:
            responses = self.gather_responses(req_type, req_id_responses)

        try:
            response_instance.handle_response(req_type, responses)
        except RuntimeError:
            # This is triggered when a codeeditor instance has been
            # removed before the response can be processed.
            pass

    def is_client_running(self, name):
        # FIXME: Espagueti
        # LanguageServerPlugin.COMPLETION_CLIENT_NAME
        if name == 'lsp':
            # The LSP plugin does not emit a plugin ready signal
            return name in self.providers

        status = self.providers.get(name, {}).get('status', self.STOPPED)
        return status == self.RUNNING

    def send_request(self, language, req_type, req):
        req_id = self.req_id
        self.req_id += 1

        self.requests[req_id] = {
            'language': language,
            'req_type': req_type,
            'response_instance': req['response_instance'],
            'sources': {},
            'timed_out': False,
        }

        # Start the timer on this request
        if self.wait_for_ms > 0:
            QTimer.singleShot(self.wait_for_ms,
                              lambda: self.receive_timeout(req_id))
        else:
            self.requests[req_id]['timed_out'] = True

        for client_name in self.providers:
            client_info = self.providers[client_name]
            client_info["provider"].send_request(
                language, req_type, req, req_id)

    def send_notification(self, language, notification_type, notification):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].send_notification(
                    language, notification_type, notification)

    def broadcast_notification(self, req_type, req):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].broadcast_notification(
                    req_type, req)

    def project_path_update(self, project_path, update_kind='addition'):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].project_path_update(
                    project_path, update_kind
                )

    def register_file(self, language, filename, codeeditor):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].register_file(
                    language, filename, codeeditor
                )

    def update_configuration(self):
        self.wait_for_ms = self.get_option('completions_wait_for_ms',
                                           section='editor')
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].update_configuration()

    def start(self):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.STOPPED:
                client_info["provider"].start()

    def shutdown(self):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].shutdown()

    def start_client(self, language):
        started = False
        language_clients = self.language_status.get(language, {})
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_started = client_info["provider"].start_client(language)
                started |= client_started
                language_clients[client_name] = client_started

        self.language_status[language] = language_clients
        return started

    def stop_client(self, language):
        for client_name in self.providers:
            client_info = self.providers[client_name]
            if client_info['status'] == self.RUNNING:
                client_info["provider"].stop_client(language)
        self.language_status.pop(language)

    def get_client(self, name):
        return self.providers[name]["provider"]

    @Slot(str)
    def client_available(self, client_name):
        client_info = self.providers[client_name]
        client_info['status'] = self.RUNNING

    # --- New API
    # ------------------------------------------------------------------------
    def set_wait_for_source_requests(self, provider_id, request_types):
        """
        Set which request types should wait for source.

        Parameters
        ----------
        provider_id: str
            Unique string identifier of the provider.
        request_types: list
            List of spyder.plugins.completion.manager.api.LSPRequestTypes.
        """
        if provider_id not in self.providers:
            raise KeyError("Invalid provider id!")

        wait_for_source = self.get_option("wait_for_source")
        for request_type in request_types:
            sources_for_req_type = wait_for_source.get(request_type, set())
            sources_for_req_type.add(provider_id)
            wait_for_source[request_type] = sources_for_req_type

        self.set_option("wait_for_source", wait_for_source)

    def set_request_type_priority(self, provider_id, request_type):
        """
        Set request type top priority for given provider.

        Parameters
        ----------
        provider_id: str
            Unique string identifier of the provider.
        request_type: str
            See spyder.plugins.completion.manager.api.LSPRequestTypes.
        """
        source_priority = self.get_option("source_priority")
        if provider_id not in self.providers:
            raise KeyError("Invalid provider id!")

        priorities = source_priority.get(
            request_type,
            self.get_provider_ids(),
        )
        priorities.remove(provider_id)
        priorities.insert(0, provider_id)
        source_priority[request_type] = priorities
        self.set_option("source_priority", source_priority)

    def get_provider_ids(self):
        """
        Return completion provider ids.
        """
        return list(self.providers.keys())
