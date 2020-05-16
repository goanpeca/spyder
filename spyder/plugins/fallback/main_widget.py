# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Fallback completion plugin.

Wraps FallbackActor to provide compatibility with SpyderCompletionPlugin API.
"""

# Standard library imports
import logging

# Third party modules
from qtpy.QtCore import Signal

# Local imports
from spyder.api.widgets import PluginWidget
from spyder.plugins.completion.api import SpyderCompletionMixin
from spyder.plugins.fallback.actor import FallbackActor


logger = logging.getLogger(__name__)


class FallbackClient(PluginWidget, SpyderCompletionMixin):
    DEFAULT_OPTIONS = {
        'enable': True,
    }

    # Signals
    sig_response_ready = Signal(str, int, dict)
    sig_plugin_ready = Signal(str)

    def __init__(self, name, plugin, parent=None, options=DEFAULT_OPTIONS):
        super().__init__(name, plugin, parent=parent, options=options)

        self.started = False
        self.requests = {}
        self.fallback_actor = FallbackActor(self)

        # Signals
        self.fallback_actor.sig_fallback_ready.connect(
            lambda: self.sig_plugin_ready.emit(name))
        self.fallback_actor.sig_set_tokens.connect(
            lambda _id, resp: self.sig_response_ready.emit(name, _id, resp))

        self.update_configuration()

    # --- PluginWidget API
    # ------------------------------------------------------------------------
    def setup(self, options=DEFAULT_OPTIONS):
        pass

    def on_option_update(self, option, value):
        pass

    def update_actions(self):
        pass

    # --- SpyderCompletionMixin API
    # ------------------------------------------------------------------------
    def start_client(self, language):
        return self.started

    def start(self):
        if not self.started and self.enabled:
            self.fallback_actor.start()
            self.started = True

    def shutdown(self):
        if self.started:
            self.fallback_actor.stop()

    def send_request(self, language, req_type, req, req_id=None):
        if not self.enabled:
            return

        request = {
            'type': req_type,
            'file': req['file'],
            'id': req_id,
            'msg': req
        }
        req['language'] = language
        self.fallback_actor.sig_mailbox.emit(request)

    def update_configuration(self):
        self.enabled = self.get_option('enable')
        self.start()

    def register_file(self, language, filename, codeeditor):
        pass
