# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite completion container."""

import os.path as osp

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.translations import get_translation
from spyder.api.widgets import PluginMainContainer
from spyder.config.base import running_under_pytest
from spyder.plugins.completion.kite.utils.status import (
    check_if_kite_running, check_if_kite_installed)
from spyder.plugins.completion.kite.provider import KiteProvider
from spyder.plugins.completion.kite.widgets.install import KiteInstallerDialog
from spyder.plugins.completion.kite.widgets.status import KiteStatusWidget
from spyder.widgets.helperwidgets import MessageCheckBox
from spyder.plugins.completion.kite.utils.install import (
    KiteInstallationThread)
from spyder.plugins.completion.kite.widgets.install import KiteInstallerDialog
from spyder.plugins.completion.kite.widgets.status import KiteStatusWidget


_ = get_translation("spyder")


class KiteContainer(PluginMainContainer):
    DEFAULT_OPTIONS = {
        "enable": True,
        "call_to_action": False,
        "show_installation_dialog": False,
        "show_onboarding": False,
        "show_installation_error_message": True,
        "code_snippets": True,
    }

    def __init__(self, name, plugin, parent=None, options=DEFAULT_OPTIONS):
        super().__init__(name, plugin, parent=parent, options=options)

        # FIXME:
        self._show_onboarding = False  # FIXME:?
        statusbar = plugin.main.statusBar()  # MainWindow status bar

        # Installation dialog
        self._installation_thread = KiteInstallationThread(None)
        self._installer = KiteInstallerDialog(self, self._installation_thread)
        self.provider = KiteProvider(plugin)
        self.status_widget = KiteStatusWidget(None, statusbar, plugin)

        # Signals
        self._installation_thread.sig_installation_status.connect(
            self.set_status)
        self.status_widget.sig_clicked.connect(
            self.show_installation_dialog)

        self.provider.sig__kite_onboarding.connect(self._kite_onboarding)
        self.provider.sig_show_onboarding_file_requested.connect(
            self._show_onboarding_file)
        self.provider.sig_status_updated[str].connect(self.set_status)
        self.provider.sig_status_updated[dict].connect(self.set_status)
        self.provider.sig_show_installation_dialog.connect(
            self.show_installation_dialog)
        self.provider.sig_kite_service_errored.connect(
            self._show_installation_error_message)

    # --- PluginMainContainer API
    # ------------------------------------------------------------------------
    def setup(self, options=DEFAULT_OPTIONS):
        pass

    def on_option_update(self, option, value):
        pass

    def update_actions(self):
        pass

    # --- Private API
    # ------------------------------------------------------------------------
    def _kite_onboarding(self):
        """Request the onboarding file."""
        # No need to check installed status, since the get_onboarding_file
        # call fails fast.
        if not self.get_option("enable"):
            return

        if not self._show_onboarding:
            return

        # FIXME:
        if self.plugin.main.is_setting_up:
            return

        if not self.available_languages:
            return

        # Don't send another request until this request fails.
        self._show_onboarding = False
        self.provider.perform_onboarding_request()

    @Slot(str)
    def _show_onboarding_file(self, onboarding_file):
        """
        Request opening the onboarding file retrieved from the Kite endpoint.

        This skips onboarding if onboarding is not possible yet or has already
        been displayed before.

        Parameters
        ----------
        onboarding_file: str
            Path to onboarding file.
        """
        if not onboarding_file:
            # retry
            self._show_onboarding = True
            return

        self.set_option('show_onboarding', False)

        # FIXME:
        self.plugin.main.open_file(onboarding_file)

    def _show_installation_error_message(self):
        """
        FIXME:
        """
        _installed, path = check_if_kite_installed()
        box = MessageCheckBox(icon=QMessageBox.Critical, parent=self)
        box.setWindowTitle(_("Kite installation error"))
        box.set_checkbox_text(_("Don't show again."))
        box.setStandardButtons(QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Ok)
        box.set_checked(False)
        box.set_check_visible(True)
        box.setText(
            _("It seems that your Kite installation is faulty. "
              "If you want to use Kite, please remove the "
              "directory that appears bellow, "
              "and try a reinstallation:<br><br>"
              "<code>{kite_dir}</code>").format(kite_dir=osp.dirname(path)))
        box.exec_()

        # Update checkbox based on user interaction
        self.set_option(
            'show_installation_error_message', not box.is_checked())

    # --- Public API
    # ------------------------------------------------------------------------
    # FIXME: Use better name
    @Slot()
    def mainwindow_setup_finished(self):
        """
        This is called after the main window setup finishes to show Kite's
        installation dialog and onboarding if necessary.
        """
        self._kite_onboarding()

        show_dialog = self.get_option('show_installation_dialog')
        if show_dialog:
            # Only show the dialog once at startup
            self.set_option('show_installation_dialog', False)
            self.show_installation_dialog()

    @Slot(str)
    @Slot(dict)
    def set_status(self, status):
        """
        Show Kite status for the current file.

        Parameters
        ----------
        status: str or dict
            FIXME:
        """
        self.status_widget.set_value(status)

    @Slot()
    def show_installation_dialog(self):
        """Show installation dialog."""
        installed, _path = check_if_kite_installed()
        if not installed and not running_under_pytest():
            self._installer.show()

    def is_installing(self):
        """Check if an installation is taking place."""
        return (self._installation_thread.isRunning()
                and not self._installation_thread.cancelled)

    def installation_cancelled_or_errored(self):
        """Check if an installation was cancelled or failed."""
        return self._installation_thread.cancelled_or_errored()

    def send_status_request(self, filename):
        """
        Request status for the given file.

        Parameters
        ----------
        filename: str
            FIXME:
        """
        self.provider.send_status_request(filename)
