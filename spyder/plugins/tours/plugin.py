# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2009- Spyder Project Contributors
#
# Distributed under the terms of the MIT License
# (see spyder/__init__.py for details)
# -----------------------------------------------------------------------------

"""
Tours Plugin.
"""

# Local imports
from spyder.api.menus import ApplicationMenus, HelpMenuSections
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.config.base import get_safe_mode, running_under_pytest
from spyder.plugins.tours.container import ToursContainer
from spyder.plugins.tours.tours import INTRO_TOUR, TourIdentifiers

# Localization
_ = get_translation('spyder')


# --- Plugin
# ----------------------------------------------------------------------------
class Tours(SpyderPluginV2):
    """
    Tours Plugin.
    """
    NAME = 'tours'
    CONF_SECTION = NAME
    # REQUIRES = [Plugins.MainMenu]
    CONF_FILE = False
    CONTAINER_CLASS = ToursContainer

    # --- SpyderPluginV2 API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _("Interactive tours")

    def get_description(self):
        return _("Provide interative tours.")

    def get_icon(self):
        return self.create_icon('keyboard')

    def register(self):
        self.register_tour(
            TourIdentifiers.IntroductionTour,
            _("Introduction to Spyder"),
            INTRO_TOUR,
        )

        # TODO: When mainmenu plugin is available
        # help_menu = mainmenu.get_application_menu(ApplicationMenus.Help)
        # mainmenu.add_item_to_application_menu(
        help_menu = self.get_application_menu(ApplicationMenus.Help)
        self.add_item_to_application_menu(
            self.get_container().tours_menu,
            menu=help_menu,
            section="To be defined",
        )

    def on_mainwindow_visible(self):
        self.show_tour_message()

    # --- Public API
    # ------------------------------------------------------------------------
    def register_tour(self, tour_id, title, tour_data):
        """
        Register a new interactive tour on spyder.

        Parameters
        ----------
        tour_id: str
            Unique tour string identifier.
        title: str
            Localized tour name.
        tour_data: dict
            The tour steps.
        """
        self.get_container().register_tour(tour_id, title, tour_data)

    def show_tour(self, index):
        """
        Show interactive tour.

        Parameters
        ----------
        index: int
            The tour index to display.
        """
        self.main.maximize_dockwidget(restore=True)
        self.get_container().show_tour(index)

    def show_tour_message(self, force=False):
        """
        Show message about starting the tour the first time Spyder starts.

        Parameters
        ----------
        force: bool
            Force the display of the tour message.
        """
        should_show_tour = self.get_conf_option('show_tour_message')
        if force or (should_show_tour and not running_under_pytest()
                     and not get_safe_mode()):
            self.set_conf_option('show_tour_message', False)
            self.get_container().show_tour_message()
