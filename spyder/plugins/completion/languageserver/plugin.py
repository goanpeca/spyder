# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Fallback completion plugin.
"""

# Local imports
import glob
import logging
import os
import os.path as osp
import re

# Third party imports
import psutil

# Local imports
from spyder.api.translations import get_translation
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.menus import ApplicationMenus, ToolsMenuSections
from spyder.api.widgets.menus import SpyderMenu
from spyder.config.base import get_conf_path, get_debug_level
from spyder.plugins.completion.languageserver.provider import (
    LanguageServerProvider)
from spyder.plugins.completion.manager.api import LSPRequestTypes
from spyder.plugins.completion.languageserver.confpage import (
    LanguageServerConfigPage)

# Localization
_ = get_translation("spyder")
logger = logging.getLogger(__name__)


class LanguageServerPlugin(SpyderPluginV2):
    NAME = 'lsp'
    REQUIRES = [Plugins.CompletionManager]
    OPTIONAL = [Plugins.Editor]
    CONF_WIDGET_CLASS = LanguageServerConfigPage
    CONF_SECTION = 'lsp-server'
    CONF_FILE = False

    # --- SpyderPluginV2 API
    #  -----------------------------------------------------------------------
    def get_name(self):
        return _('Language server completions')

    def get_description(self):
        return _('Language server completions')

    def get_icon(self):
        return self.create_icon('lspserver')

    def register(self):
        # FIXME: Temporal hack
        LanguageServerProvider._main = self.main

        self.provider = LanguageServerProvider(self)
        completion_manager = self.get_plugin(Plugins.CompletionManager)
        completion_manager.register_completion_provider(
            self.provider)
        completion_manager.set_wait_for_source_requests(
            LanguageServerProvider.ID,
            [
                LSPRequestTypes.DOCUMENT_COMPLETION,
                LSPRequestTypes.DOCUMENT_SIGNATURE,
                LSPRequestTypes.DOCUMENT_HOVER,
            ]
        )

        if get_debug_level() >= 3:
            tools_menu = self.get_application_menu(ApplicationMenus.Tools)
            # Move this to the container
            self.menu_lsp_logs = SpyderMenu(self.main, _("LSP logs"))
            self.add_item_to_application_menu(
                self.menu_lsp_logs,
                menu=tools_menu,
                section=ToolsMenuSections.Tools,
            )
            self.menu_lsp_logs.aboutToShow.connect(self.update_lsp_logs)

    def on_mainwindow_visible(self):
        logger.info('Deleting previous Spyder instance LSP logs...')
        self._delete_lsp_log_files()

        completion_manager = self.get_plugin(Plugins.CompletionManager)
        lsp_provider = completion_manager.get_client("lsp")
        lsp_provider.on_mainwindow_setup_finished()

    # --- Private API
    # -----------------------------------------------------------------------
    def _delete_lsp_log_files(self):
        """Delete previous dead Spyder instances LSP log files."""
        regex = re.compile(r'.*_.*_(\d+)[.]log')
        files = glob.glob(osp.join(get_conf_path('lsp_logs'), '*.log'))
        for f in files:
            match = regex.match(f)
            if match is not None:
                pid = int(match.group(1))
                if not psutil.pid_exists(pid):
                    os.remove(f)

    # FIXME:
    def update_lsp_logs(self):
        """Create an action for each lsp log file."""
        self.menu_lsp_logs.clear()
        lsp_logs = []
        files = glob.glob(osp.join(get_conf_path('lsp_logs'), '*.log'))
        for f in files:
            action = self.create_action(
                self,
                f,
                # FIXME: need to use a global signal, editor depends on completions?
                # but not on language server so this could depend optionally on it?
                triggered=self.editor.load,
            )
            action.setData(f)
            lsp_logs.append(action)

        print(lsp_logs)
        # add_actions(self.menu_lsp_logs, lsp_logs)
