# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Fallback completion plugin.
"""

# Third party imports
from qtpy.QtGui import QIcon

# Local imports
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.completion.fallback.provider import FallbackProvider


# Localization
_ = get_translation("spyder")


class FallbackPlugin(SpyderPluginV2):
    NAME = FallbackProvider.ID
    REQUIRES = [Plugins.CompletionManager]
    OPTIONAL = []
    CONF_SECTION = 'fallback-completions'
    CONF_FILE = False

    # --- SpyderPluginV2 API
    #  -----------------------------------------------------------------------
    def get_name(self):
        return _('Fallback completions')

    def get_description(self):
        return _('Fallback completions')

    def get_icon(self):
        return QIcon()

    def register(self):
        completion_manager = self.get_plugin(Plugins.CompletionManager)
        completion_manager.register_completion_provider(
            FallbackProvider(self))
