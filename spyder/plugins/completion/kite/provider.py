# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite completion provider."""

# Standard library imports
import functools
import logging

# Third party imports
from qtpy.QtCore import Signal, Slot

# Local imports
from spyder.config.manager import CONF  # FIXME: Remove!
from spyder.plugins.completion.kite.client import KiteClient
from spyder.plugins.completion.kite.utils.status import (
    check_if_kite_installed, check_if_kite_running)
from spyder.plugins.completion.manager.api import BaseCompletionProvider
from spyder.utils.programs import run_program


logger = logging.getLogger(__name__)


class KiteProvider(BaseCompletionProvider):
    ID = 'kite'

    # --- Signals
    # ------------------------------------------------------------------------
    sig_kite_service_errored = Signal(Exception)
    """
    This signal can be emitter to inform that an error on the Kite
    process/service ocurred.

    Paramaters
    ----------
    exception: Exception
        The exception that occured.
    """

    sig__kite_onboarding = Signal()
    """
    FIXME
    """

    sig_show_onboarding_file_requested = Signal(str)
    """
    This signal is emitted to request to show the onboarding file.

    Parameters
    ----------
    filepath: str
        Path to onboarding file.
    """

    sig_status_updated = Signal((str,), (dict,))
    """
    FIXME:

    Paramaters
    ----------
    status: str or dict
        FIXME:
    """

    sig_show_installation_dialog = Signal()
    """
    FIXME
    """

    def __init__(self, plugin):
        super().__init__(plugin)

        self._available_languages = []
        self._kite_process = None
        self._client = KiteClient(None)

        # Signals
        self._client.sig_client_started.connect(self._http_client_ready)
        self._client.sig_onboarding_response_ready.connect(
            lambda: self.sig_show_onboarding_file.emit())
        self._client.sig_response_ready.connect(
            lambda: self.sig__kite_onboarding.emit())
        self._client.sig_response_ready.connect(
            functools.partial(self.sig_response_ready.emit, self.ID))
        self._client.sig_status_response_ready[str].connect(
            self.sig_status_updated[str])
        self._client.sig_status_response_ready[dict].connect(
            self.sig_status_updated[dict])
        self._client.sig_status_response_ready.connect(
            lambda: self.sig__kite_onboarding.emit())

        # FIXME: Why here?
        self.update_configuration()

    # --- Private API
    # ------------------------------------------------------------------------
    @Slot(list)
    def _http_client_ready(self, languages):
        """
        Client ready callback.

        Parameters
        ----------
        languages: FIXME:
            List? of languages supported by the Kite client.
        """
        logger.debug('Kite client is available for {0}'.format(languages))
        self._available_languages = languages

        self.sig_provider_ready.emit(self.ID)
        self.sig__kite_onboarding.emit()

    # --- BaseCompletionProvider API
    # ------------------------------------------------------------------------
    def start(self):
        try:
            if not self.get_option('enable'):
                return

            installed, path = check_if_kite_installed()
            if not installed:
                return

            logger.debug('Kite was found on the system: {0}'.format(path))
            running = check_if_kite_running()
            if running:
                return

            logger.debug('Starting Kite service...')
            self._kite_process = run_program(path)
        except OSError as error:
            _installed, path = check_if_kite_installed()
            logger.debug(
                'Error starting Kite service at {path}...'.format(path=path))
            self.sig_kite_service_errored.emit(error)
        finally:
            # Always start client to support possibly undetected Kite builds
            self._client.start()

    def start_client(self, language):
        return language in self._available_languages

    def send_request(self, language, req_type, req, req_id):
        if (self.get_option('enable')
                and language in self._available_languages):
            self._client.sig_perform_request.emit(req_id, req_type, req)
        else:
            self.sig_response_ready.emit(self.ID, req_id, {})

    def shutdown(self):
        self._client.stop()
        if self._kite_process is not None:
            self._kite_process.kill()

    def update_configuration(self):
        # FIXME: So this plugin depends on the Language Server? Why?
        # Since the completion manager already assumes the LSP why not use
        # that? Then Kite can only depend on that, and not on the LSP.
        # Also this should probably be a method on _client
        self._client.enable_code_snippets = CONF.get(
            'lsp-server', 'code_snippets')

    # --- Public API
    # ------------------------------------------------------------------------
    def perform_onboarding_request(self):
        """
        Perform an onboarding request to the Kite client.
        """
        self._client.sig_perform_onboarding_request.emit()

    def send_status_request(self, filename):
        """
        Request status for the given file.

        Parameters
        ----------
        filename: str
            FIXME:
        """
        self._client.sig_perform_status_request.emit(filename)
