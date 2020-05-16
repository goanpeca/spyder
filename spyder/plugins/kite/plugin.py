# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Kite Plugin.
"""

# Third party imports
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.kite.widgets.main_widget import KiteCompletionClient
from spyder.plugins.completion.api import LSPRequestTypes


# Localization
_ = get_translation('spyder')


class Kite(SpyderPluginV2):
    """
    Kite plugin providing completions
    """
    NAME = 'kite'
    REQUIRES = [Plugins.CodeCompletion, Plugins.Editor]
    WIDGET_CLASS = KiteCompletionClient
    CONF_SECTION = NAME
    CONF_FILE = False

    OPTIONS_FROM_CONF = {
        'lsp-server': 'code_snippets',
    }

    def get_name(self):
        return _('Kite')

    def get_description(self):
        return _('Provide completions on Editor using Kite')

    def get_icon(self):
        return self.create_icon('Kite')

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
        completion.set_request_type_priority(
            self.NAME,
            LSPRequestTypes.DOCUMENT_COMPLETION,
        )
        self.add_application_status_widget(
            'kite_status', widget.status_widget)

    def on_first_registration(self):
        widget = self.get_widget()
        widget.start_kite_onboarding()

        show_dialog = self.get_conf_option('show_installation_dialog')
        if show_dialog:
            # Only show the dialog once at startup
            self.set_conf_option('show_installation_dialog', False)
            widget.show_installation_dialog()

    def on_close(self, cancelable=False):
        """
        Check if an installation is taking place.
        """
        if cancelable and self.get_widget().is_installing():
            reply = QMessageBox.critical(
                self,
                'Spyder',
                _('Kite installation process has not finished. '
                  'Do you really want to exit?'),
                QMessageBox.Yes,
                QMessageBox.No,
            )

            if reply == QMessageBox.No:
                return False

        return True
