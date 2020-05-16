# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Kite completion widget.
"""

# Standard library imports
import functools
import logging
import os

# Third party imports
from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.widgets import PluginWidget
from spyder.config.base import running_under_pytest
from spyder.plugins.completion.api import SpyderCompletionMixin
from spyder.plugins.kite.client import KiteClient
from spyder.plugins.kite.utils.install import KiteInstallationThread
from spyder.plugins.kite.utils.status import (check_if_kite_installed,
                                              check_if_kite_running)
from spyder.plugins.kite.widgets.install import KiteInstallerDialog
from spyder.plugins.kite.widgets.status import KiteStatusWidget
from spyder.utils.programs import run_program
from spyder.widgets.helperwidgets import MessageCheckBox


logger = logging.getLogger(__name__)


class KiteCompletionClient(PluginWidget, SpyderCompletionMixin):
    DEFAULT_OPTIONS = {
        'enable': True,
        'call_to_action': True,
        'code_snippets': True,
        'show_installation_dialog': True,
        'show_installation_error_message': True,
        'show_onboarding': True,
    }

    # Signals
    sig_response_ready = Signal(str, int, dict)
    sig_plugin_ready = Signal(str)

    def __init__(self, name, plugin, parent=None, options=DEFAULT_OPTIONS):
        super().__init__(name, plugin, parent=parent, options=options)

        self.available_languages = []
        self.kite_process = None
        self.open_file_updated = False
        self.name = name

        # Widgets
        self.client = KiteClient(None)
        self.installation_thread = KiteInstallationThread(self)
        self.installer = KiteInstallerDialog(parent, self.installation_thread)
        self.status_widget = KiteStatusWidget(self)

        # Signals
        self.client.sig_client_started.connect(self.http_client_ready)
        self.client.sig_status_response_ready[str].connect(
            self.set_status)
        self.client.sig_status_response_ready[dict].connect(
            self.set_status)
        self.client.sig_response_ready.connect(
            functools.partial(self.sig_response_ready.emit, name))

        self.client.sig_response_ready.connect(self.start_kite_onboarding)
        self.client.sig_status_response_ready.connect(self.start_kite_onboarding)
        self.client.sig_onboarding_response_ready.connect(
            self.show_onboarding_file)

        self.installation_thread.sig_installation_status.connect(
            self.set_status)
        self.status_widget.sig_clicked.connect(
            self.show_installation_dialog)
        # self.main.sig_setup_finished.connect(self.mainwindow_setup_finished)

        # Config
        self.update_configuration()

    @Slot(list)
    def http_client_ready(self, languages):
        logger.debug('Kite client is available for {0}'.format(languages))
        self.available_languages = languages
        self.sig_plugin_ready.emit(self.name)
        # self._kite_onboarding()

    @Slot(str)
    @Slot(dict)
    def set_status(self, status):
        """Show Kite status for the current file."""
        self.status_widget.set_value(status)

    @Slot()
    def show_installation_dialog(self):
        """Show installation dialog."""
        installed, __ = check_if_kite_installed()
        if not installed and not running_under_pytest():
            self.installer.show()

    def send_request(self, language, req_type, req, req_id):
        if self.enabled and language in self.available_languages:
            self.client.sig_perform_request.emit(req_id, req_type, req)
        else:
            self.sig_response_ready.emit(self.name,
                                         req_id, {})

    def send_status_request(self, filename):
        """Request status for the given file."""
        if not self.is_installing():
            self.client.sig_perform_status_request.emit(filename)

    # --- API for SpyderPlugin
    # ------------------------------------------------------------------------
    def setup(self, options=DEFAULT_OPTIONS):
        pass

    def on_option_update(self, value, option):
        pass

    def update_actions(self):
        pass

    # --- API for completion mixin
    # ------------------------------------------------------------------------
    def start_client(self, language):
        return language in self.available_languages

    def stop_client(self, language):
        pass

    def start(self):
        try:
            if not self.enabled:
                return

            installed, path = check_if_kite_installed()
            if not installed:
                return

            logger.debug('Kite was found on the system: {0}'.format(path))
            running = check_if_kite_running()
            if running:
                return

            logger.debug('Starting Kite service...')
            self.kite_process = run_program(path)
        except OSError:
            installed, path = check_if_kite_installed()
            logger.debug(
                'Error starting Kite service at {path}...'.format(path=path))
            if self.get_option('show_installation_error_message'):
                box = MessageCheckBox(
                    icon=QMessageBox.Critical, parent=self)
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
                      "<code>{kite_dir}</code>".format(
                          kite_dir=os.path.dirname(path))))

                box.exec_()

                # Update checkbox based on user interaction
                self.set_option(
                    'show_installation_error_message', not box.is_checked())
        finally:
            # Always start client to support possibly undetected Kite builds
            self.client.start()

    def shutdown(self):
        self.client.stop()
        if self.kite_process is not None:
            self.kite_process.kill()

    def update_configuration(self):
        self.client.enable_code_snippets = self.get_option('code_snippets')
        self.enabled = self.get_option('enable')
        self._show_onboarding = self.get_option('show_onboarding')

    def register_file(self, language, filename, codeeditor):
        pass

    def send_notification(self, language, notification_type, notification):
        pass

    def send_response(self, response, resp_id):
        pass

    def broadcast_notification(self, notification_type, notification):
        pass

    def project_path_update(self, project_path, update_kind):
        pass

    # --- API
    # ------------------------------------------------------------------------
    def is_installing(self):
        """Check if an installation is taking place."""
        return (self.installation_thread.isRunning()
                and not self.installation_thread.cancelled)

    def installation_cancelled_or_errored(self):
        """Check if an installation was cancelled or failed."""
        return self.installation_thread.cancelled_or_errored()

    def start_kite_onboarding(self):
        """Request the onboarding file."""
        # No need to check installed status,
        # since the get_onboarding_file call fails fast.
        if not self.enabled:
            return

        if not self._show_onboarding:
            return

        # if self.main.is_setting_up:
        #     return

        if not self.available_languages:
            return

        # Don't send another request until this request fails.
        self._show_onboarding = False
        self.client.sig_perform_onboarding_request.emit()

    @Slot(str)
    def show_onboarding_file(self, onboarding_file):
        """
        Opens the onboarding file, which is retrieved
        from the Kite HTTP endpoint. This skips onboarding if onboarding
        is not possible yet or has already been displayed before.
        """
        if not onboarding_file:
            # Retry
            self._show_onboarding = True
            return

        self.set_option('show_onboarding', False)
        # self.main.open_file(onboarding_file)
