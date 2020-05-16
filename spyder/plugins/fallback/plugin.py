# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Fallback completion plugin.

Wraps FallbackActor to provide compatibility with SpyderCompletionPlugin API.
"""

# Standard library imports

from qtpy.QtGui import QIcon

# Local imports
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.fallback.main_widget import FallbackClient


# Localization
_ = get_translation('spyder')


class Fallback(SpyderPluginV2):
    NAME = 'fallback'
    REQUIRES = [Plugins.CodeCompletion]
    OPTIONAL = [Plugins.KiteCompletion]
    WIDGET_CLASS = FallbackClient
    CONF_SECTION = 'fallback-completions'
    CONF_FILE = False

    def get_name(self):
        return _('Fallback')

    def get_description(self):
        return _('Fallback code completion client')

    def get_icon(self):
        return QIcon()

    def register(self):
        completion = self.get_plugin(Plugins.CodeCompletion)
        completion.register_completion_client(self.NAME, self.get_widget())
