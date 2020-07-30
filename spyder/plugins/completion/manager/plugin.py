# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Plugin to manage multiple code completion and introspection providers.
"""

# Third-party imports
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.plugins import SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.completion.manager.api import WorkspaceUpdateKind
from spyder.plugins.completion.manager.container import (
    CompletionManagerContainer)

# Localization
_ = get_translation("spyder")


class CompletionManager(SpyderPluginV2):
    NAME = 'completion_manager'
    REQUIRES = []
    OPTIONAL = []
    CONTAINER_CLASS = CompletionManagerContainer
    CONF_SECTION = NAME
    CONF_FILE = False

    # --- Signals
    # ------------------------------------------------------------------------
    sig_provider_started = Signal(str)
    """
    This signal is emitted to inform a registered completion provider has
    started and is ready to provide completions.

    Parameters
    ----------
    provider_id: str
        FIXME:
    """

    sig_provider_response_received = Signal(str, int, dict)
    """
    This signal is emitted when a provider has sent a response to the
    completion manager.

    Parameters
    ----------
    provider_id: str
        FIXME:
    response_type: int
        FIXME:
    parameters: dict
        FIXME:
    """

    # --- SpyderPluginV2 API
    #  -----------------------------------------------------------------------
    def get_name(self):
        return _('Code completion manager')

    def get_description(self):
        return _('Code completion manager')

    def get_icon(self):
        return self.create_icon('help')  # FIXME:

    def register(self):
        pass

    def on_mainwindow_visible(self):
        self.start_providers()
        self.start_provider_clients(language='python')

    def on_close(self, cancelable=False):
        self.shutdown_providers()
        return True

    # --- Public API
    # ------------------------------------------------------------------------
    def register_completion_provider(self, provider):
        """
        Register a completion provider instance.

        Parameters
        ----------
        provider: BaseCompletionProvider
            The completion provider instance.
        """
        self.get_container().register_completion_provider(provider)

    def set_wait_for_source_requests(self, provider_id, request_types):
        """
        Set which request types should wait for source.

        Parameters
        ----------
        provider_id: str
            Unique string identifier of the provider.
        request_types: list
            List of spyder.plugins.completion.api.LSPRequestTypes.
        """
        self.get_container().set_wait_for_source_requests(
            provider_id, request_types)

    def set_request_type_priority(self, provider_id, request_type):
        """
        Set request type top priority for given provider.

        Parameters
        ----------
        provider_id: str
            Unique string identifier of the provider.
        request_type: str
            See `spyder.plugins.completion.api.LSPRequestTypes`
        """
        self.get_container().set_wait_for_source_requests(
            provider_id, request_type)

    def get_provider(self, provider_id):
        """
        Return a registered completion by `provider_id`.

        Parameters
        ----------
        provider_id: str
            Provider unique string identifier.
        """
        return self.get_container().get_client(provider_id)

    def start_providers(self):
        """
        Start all registered completion providers.
        """
        self.get_container().start()

    def start_provider_clients(self, language):
        """
        Start a specific `language` client for all registered completion
        providers.

        Returns
        -------
        bool
            FIXME:
        """
        return self.get_container().start_client(language)

    def shutdown_providers(self):
        """
        Shutdown all registered completion providers.
        """
        self.get_container().shutdown()

    def update_project_path(self, project_path,
                            update_kind=WorkspaceUpdateKind.ADDITION):
        """
        FIXME:

        Parameters
        ----------
        project_path: str
            Root path of updated project.
        update_kind: str, optional
            Type of project update. Default is "addition".
        """
        self.get_container().project_path_update(project_path,
                                                 update_kind=update_kind)

    def register_file(self, language, filename, codeeditor):
        """
        Register a `filename` of a given `codeeditor` and `language` for
        completion services.

        Parameters
        ----------
        language: str
            Type of language registered for completion services.
        filename: str
            Full path to file registered for completion services.
        codeeditor: spyder.editor.widgets.codeeditor.CodeEditor
            FIXME:
        """
        self.get_container().register_file(language, filename, codeeditor)

    def send_request(self, language, request, params):
        """
        Send a request to all registered completion providers.

        Parameters
        ----------
        language: str
            FIXME:
        request: FIXME:
            FIXME:
        params: dict:
            FIXME:
        """
        self.get_container().send_request(language, request, params)
