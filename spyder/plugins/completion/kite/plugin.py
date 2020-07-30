# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite completion provider plugin."""

# Third party imports
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.menus import ApplicationMenus, ToolsMenuSections
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.completion.kite.container import KiteContainer
from spyder.plugins.completion.kite.utils.install import (
    check_if_kite_installed)
from spyder.plugins.completion.manager.api import LSPRequestTypes

# Localization
_ = get_translation("spyder")


class KitePlugin(SpyderPluginV2):
    NAME = 'kite'
    REQUIRES = [Plugins.CompletionManager]
    OPTIONAL = []
    CONTAINER_CLASS = KiteContainer
    CONF_SECTION = 'kite'
    CONF_FILE = False

    # --- SpyderPluginV2 API
    #  -----------------------------------------------------------------------
    def get_name(self):
        return _('Kite completions')

    def get_description(self):
        return _('Kite completions')

    def get_icon(self):
        return self.create_icon('kite')

    def register(self):
        container = self.get_container()
        completion_manager = self.get_plugin(Plugins.CompletionManager)
        completion_manager.register_completion_provider(container.provider)
        completion_manager.set_wait_for_source_requests(
            container.provider.ID,
            [
                LSPRequestTypes.DOCUMENT_COMPLETION,
                LSPRequestTypes.DOCUMENT_SIGNATURE,
                LSPRequestTypes.DOCUMENT_HOVER,
            ]
        )
        completion_manager.set_request_type_priority(
            container.provider.ID,
            LSPRequestTypes.DOCUMENT_COMPLETION,
        )

        # Add application menu entry
        is_kite_installed, _kite_path = check_if_kite_installed()
        if not is_kite_installed:
            install_kite_action = self.create_action(
                "kite_install_action",
                text=_("Install Kite completion engine"),
                # icon=self.create_icon("kite"),
                triggered=self.show_kite_installation,
            )
            tools_menu = self.get_application_menu(ApplicationMenus.Tools)
            self.add_item_to_application_menu(
                install_kite_action,
                menu=tools_menu,
                section=ToolsMenuSections.Tools,
            )

    def on_close(self, cancelable=False):
        if cancelable and self.provider.is_installing():
            reply = QMessageBox.critical(
                self.main,
                'Spyder',
                _('Kite installation process has not finished. '
                  'Do you really want to exit?'),
                QMessageBox.Yes,
                QMessageBox.No,
            )

            if reply == QMessageBox.No:
                return False

        return True

    def on_mainwindow_visible(self):
        is_kite_installed, _kite_path = check_if_kite_installed()
        if is_kite_installed:
            self.provider.mainwindow_setup_finished()
        else:
            self.show_kite_installation()

    # --- Public API
    # ------------------------------------------------------------------------
    def show_kite_installation(self):
        """
        Show the Kite installation dialog.
        """
        self.provider.show_installation_dialog()

    def send_status_request(self, filename):
        """
        Request status for the given file.

        Parameters
        ----------
        filename: str
            FIXME:
        """
        container = self.get_container()
        if not self.is_installing():
            container.send_status_request(filename)

    def is_installing(self):
        """
        Return if Kite is currently being installed.

        Returns
        -------
        bool
            Wheter Kite is currently being installed or not.
        """
        container = self.get_container()
        if container is None:
            result = True
        else:
            result = container.is_installing()

        return result

    def installation_cancelled_or_errored(self):
        """
        Return if Kite installation was cancelled or errored.

        Returns
        -------
        bool
            Installation cancel/error state.
        """
        container = self.get_container()
        if container is None:
            result = False
        else:
            result = container.installation_cancelled_or_errored()

        return result
