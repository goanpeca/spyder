# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Fallback completion provider.
"""

# Local imports
from spyder.plugins.completion.manager.api import BaseCompletionProvider
from spyder.plugins.completion.fallback.actor import FallbackActor


class FallbackProvider(BaseCompletionProvider):
    ID = 'fallback'

    def __init__(self, parent):
        super().__init__(parent)

        self._fallback_actor = FallbackActor(self)
        self._started = False

        # Signals
        self._fallback_actor.sig_fallback_ready.connect(
            lambda: self.sig_provider_ready.emit(self.ID))
        self._fallback_actor.sig_set_tokens.connect(
            lambda _id, resp: self.sig_response_ready.emit(
                self.ID, _id, resp))

        # FIXME: Why here?
        self.update_configuration()

    # --- BaseCompletionProvider API
    # ------------------------------------------------------------------------
    def start(self):
        if not self._started and self.get_option('enable'):
            self._fallback_actor.start()
            self._started = True

    def start_client(self, language):
        return self._started

    def send_request(self, language, req_type, req, req_id=None):
        if self.get_option('enable'):
            request = {
                'type': req_type,
                'file': req['file'],
                'id': req_id,
                'msg': req
            }
            req['language'] = language
            self._fallback_actor.sig_mailbox.emit(request)

    def shutdown(self):
        if self._started:
            self._fallback_actor.stop()

    def update_configuration(self):
        pass

        # FIXME: Why here?
        self.start()
