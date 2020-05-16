# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Completion plugin to manage code completion and introspection clients.
"""

# Third party imports
from qtpy.QtGui import QIcon

# Local imports
from spyder.api.plugins import SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.completion.main_widget import CodeCompletionManagerWidget


# Localization
_ = get_translation('spyder')


class CodeCompletion(SpyderPluginV2):
    """
    Completion plugin to manage code completion and introspection clients.
    """
    NAME = 'completions'
    REQUIRES = []
    OPTIONAL = []
    WIDGET_CLASS = CodeCompletionManagerWidget
    CONF_SECTION = NAME
    CONF_FILE = False
    CONF_FROM_OPTIONS = {
        'wait_completions_for_ms': ('editor', 'wait_completions_for_ms'),
    }

    # --- SpyderPlugin API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _('Completions')

    def get_description(self):
        return _('Provide completions management on Editor')

    def get_icon(self):
        # FIXME:
        return QIcon()

    def register(self):
        # FIXME: Connect signals of widget
        pass

    # --- API
    # ------------------------------------------------------------------------
    def register_completion_client(self, name, client):
        self.get_widget().register_completion_client(name, client)

    def set_wait_for_source_requests(self, name, request_types):
        self.get_widget().set_wait_for_source_requests(name, request_types)

    def set_request_type_priority(self, name, request_type):
        self.get_widget().set_wait_for_source_requests(name, request_type)

    def start(self):
        self.get_widget().start()

    def start_client(self, language):
        self.get_widget().start_client(language)

    def register_file(self, language, filename, codeeditor):
        self.get_widget().register_file(language, filename, codeeditor)

    @property
    def project_path_update(self):
        pass
