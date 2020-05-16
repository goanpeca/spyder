# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Manager for all LSP clients connected to the servers defined in Preferences.
"""

# Third party modules
from qtpy.QtCore import Signal
from qtpy.QtGui import QIcon

# Local modules
from spyder.api.translations import get_translation
from spyder.api.plugins import SpyderPluginV2, Plugins
from spyder.plugins.languageserver.confpage import LanguageServerConfigPage
from spyder.plugins.languageserver.main_widget import LanguageServerClient
from spyder.plugins.completion.api import LSPRequestTypes


# Localization
_ = get_translation('spyder')


class LanguageServer(SpyderPluginV2):
    """
    Language server completion client plugin.
    """
    NAME = 'lsp'
    REQUIRES = [Plugins.CodeCompletion, Plugins.Editor]
    OPTIONAL = []
    WIDGET_CLASS = LanguageServerClient
    CONF_SECTION = 'lsp-server'
    CONF_FILE = False
    CONF_WIDGET_CLASS = LanguageServerConfigPage
    CONF_FROM_OPTIONS = {
        'spyder_pythonpath': ('main', 'spyder_pythonpath'),
        'custom_interpreter': ('main_interpreter', 'custom_interpreter'),
        'default_interpreter': ('main_interpreter', 'default'),
    }

    # Signals
    sig_response_ready = Signal(str, int, dict)
    sig_plugin_ready = Signal(str)

    # --- SpyderPlugin API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _('Language server completion client')

    def get_description(self):
        return _('Provide language server completions')

    def get_icon(self):
        # FIXME:
        return QIcon()

    def register(self):
        widget = self.get_widget()

        completion = self.get_plugin(Plugins.CodeCompletion)
        completion.register_completion_client(self.NAME, widget)
        completion.set_wait_for_source_requests(
            self.NAME,
            [
                LSPRequestTypes.DOCUMENT_COMPLETION,
                LSPRequestTypes.DOCUMENT_SIGNATURE,
                LSPRequestTypes.DOCUMENT_HOVER,
            ]
        )

    # --- API
    # ------------------------------------------------------------------------
    def register_completion_client(self, name, client):
        self.get_widget().register_completion_client(name, client)

    def start(self):
        self.get_widget().start()

    def start_client(self, language):
        self.get_widget().start_client(language)

    def register_file(self, language, filename, codeeditor):
        self.get_widget().register_file(language, filename, codeeditor)

    @property
    def project_path_update(self):
        pass
