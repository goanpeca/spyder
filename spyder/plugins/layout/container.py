# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Layout container.
"""

# Local imports
from collections import OrderedDict

# Third party imports
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.exceptions import SpyderAPIError
from spyder.api.translations import get_translation
from spyder.api.widgets import PluginMainContainer
from spyder.plugins.layout.api import BaseGridLayoutType
from spyder.plugins.layout.widgets.dialog import (LayoutSaveDialog, LayoutSettingsDialog)

# Localization
_ = get_translation("spyder")

# Constants
DEFAULT_LAYOUTS = 4


class ToggleLayoutDirection:
    Next = "next_Layout"
    Previous = "previous_layout"


class LayoutContainerActions:
    DefaultLayout = 'default_layout_action'
    MatlabLayout = 'matlab_layout_action'
    RStudio = 'rstudio_layout_action'
    HorizontalSplit = 'horizontal_split_layout_action'
    VerticalSplit = 'vertical_split_layout_action'
    SaveLayoutAction = 'save_layout_action'
    ShowLayoutPreferencesAction = 'show_layout_preferences_action'
    ResetLayout = 'reset_layout_action'


class LayoutContainer(PluginMainContainer):

    DEFAULT_OPTIONS = {
        "place_holder": "",
        "names": ["Matlab layout", "Rstudio layout", "Vertical split", "Horizontal split"],
        "order": ["Matlab layout", "Rstudio layout", "Vertical split", "Horizontal split"],
        "active": ["Matlab layout", "Rstudio layout", "Vertical split", "Horizontal split"],
        # Main application window 
        # 'size': None,
        # 'prefs_dialog_size': None,
        # 'is_maximized': None,
        # 'is_fullscreen': None,
        # 'position': None,
        # 'state': None,
        # 'statusbar': None,
    }

    def __init__(self, name, plugin, parent=None, options=DEFAULT_OPTIONS):
        super().__init__(name, plugin, parent=parent, options=options)

        self._spyder_layouts = OrderedDict()
        self._main_window = None
        self._save_dialog = None
        self._settings_dialog = None
        self._layouts_menu = None

    # --- PluginMainContainer API
    # ------------------------------------------------------------------------
    def setup(self, options=DEFAULT_OPTIONS):

        # # Maximize current plugin
        # self.maximize_action = create_action(self, '',
        #                                 triggered=self.maximize_dockwidget,
        #                                 context=Qt.ApplicationShortcut)
        # self.register_shortcut(self.maximize_action, "_", "Maximize pane")
        # self.__update_maximize_action()

        # # Fullscreen mode
        # self.fullscreen_action = create_action(self,
        #                                 _("Fullscreen mode"),
        #                                 triggered=self.toggle_fullscreen,
        #                                 context=Qt.ApplicationShortcut)
        # self.register_shortcut(self.fullscreen_action, "_",
        #                        "Fullscreen mode", add_shortcut_to_tip=True)

        # Create default layouts for the menu
        self._default_layout_action = self.create_action(
            LayoutContainerActions.DefaultLayout,
            text=_('Spyder Default Layout'),
            triggered=lambda: self.quick_layout_switch('default'),
            register_shortcut=False,
        )
        self._save_layout_action = self.create_action(
            LayoutContainerActions.SaveLayoutAction,
            _("Save current layout"),
            triggered=lambda: self.show_save_layout(),
            context=Qt.ApplicationShortcut,
            register_shortcut=False,
        )
        self._show_preferences_action = self.create_action(
            LayoutContainerActions.ShowLayoutPreferencesAction,
            text=_("Layout preferences"),
            triggered=lambda: self.show_layout_settings(),
            context=Qt.ApplicationShortcut,
            register_shortcut=False,
        )
        self._reset_action = self.create_action(
            LayoutContainerActions.ResetLayout,
            text=_('Reset to spyder default'),
            triggered=self.reset_window_layout,
            register_shortcut=False,
        )

        # # custom layouts shortcuts
        # self.toggle_next_layout_action = create_action(self,
        #                             _("Use next layout"),
        #                             triggered=self.toggle_next_layout,
        #                             context=Qt.ApplicationShortcut)
        # self.toggle_previous_layout_action = create_action(self,
        #                             _("Use previous layout"),
        #                             triggered=self.toggle_previous_layout,
        #                             context=Qt.ApplicationShortcut)
        # self.register_shortcut(self.toggle_next_layout_action, "_",
        #                        "Use next layout")
        # self.register_shortcut(self.toggle_previous_layout_action, "_",
        #                        "Use previous layout")

        # Layouts menu
        self._layouts_menu = self.create_menu("layouts_menu", _("Window layouts"))

        # Signals
        self.update_actions()

    def on_option_update(self, option, value):
        pass

    def update_actions(self):
        menu = self._layouts_menu
        menu.clear()
        names = self.get_option('names')
        order = self.get_option('order')
        active = self.get_option('active')

        actions = [self._default_layout_action]
        for name in order:
            if name in active:
                index = names.index(name)

                # closure required so lambda works with the default parameter
                def trigger(i=index, self=self):
                    return lambda: self.quick_layout_switch(i)

                try:
                    layout_switch_action = self.create_action(
                        name,
                        text=name,
                        triggered=trigger(),
                        register_shortcut=False,
                    )
                except SpyderAPIError:
                    layout_switch_action = self.get_action(name)

                actions.append(layout_switch_action)

        for item in actions:
            self.add_item_to_menu(item, menu, section="layouts_section")

        for item in [self._save_layout_action, self._show_preferences_action,
                     self._reset_action]:
            self.add_item_to_menu(item, menu, section="layouts_section_2")

        self._show_preferences_action.setEnabled(len(order) != 0)

    # --- Public API
    # ------------------------------------------------------------------------
    def set_main_window(self, main_window):
        """
        FIXME:
        """
        self._main_window = main_window

    def register_layout(self, parent_plugin, layout_type):
        """
        Register a new layout type.

        Parameters
        ----------
        parent_plugin: spyder.api.plugins.SpyderPluginV2
            Plugin registering the layout type.
        layout_type: spyder.plugins.layout.api.BaseGridLayoutType
            Layout to regsiter.
        """
        if not issubclass(layout_type, BaseGridLayoutType):
            raise SpyderAPIError(
                "A layout must be a subclass is `BaseGridLayoutType`!")

        layout_id = layout_type.ID
        if layout_id in self._spyder_layouts:
            raise SpyderAPIError(
                "Layout with id `{}` already registered!".format(layout_id))

        layout = layout_type(parent_plugin)
        layout._check_layout_validity()
        self._spyder_layouts[layout_id] = layout

    def show_save_layout(self):
        """Show the save layout dialog."""
        names = self.get_option('names')
        order = self.get_option('order')
        active = self.get_option('active')

        dlg = self._save_dialog = LayoutSaveDialog(self, names)

        if dlg.exec_():
            name = dlg.combo_box.currentText()
            if name in names:
                answer = QMessageBox.warning(
                    self,
                    _("Warning"),
                    _("Layout <b>{0}</b> will be overwritten."
                      "Do you want to continue?".format(name)),
                    QMessageBox.Yes | QMessageBox.No,
                )
                index = order.index(name)
            else:
                answer = True
                if None in names:
                    index = names.index(None)
                    names[index] = name
                else:
                    index = len(names)
                    names.append(name)

                order.append(name)

            # Always make active a new layout even if it overwrites an
            # inactive layout
            if name not in active:
                active.append(name)

            if answer:
                self.save_current_window_settings('layout_{}/'.format(index),
                                                  section='quick_layouts')
                self.set_option('names', names)
                self.set_option('order', order)
                self.set_option('active', active)

            self.update_actions()

    def show_layout_settings(self):
        """Layout settings dialog."""
        names = self.get_option('names')
        order = self.get_option('order')
        active = self.get_option('active')

        dlg = self._settings_dialog = LayoutSettingsDialog(self, names, order, active)
        if dlg.exec_():
            self.set_option('names', dlg.names)
            self.set_option('order', dlg.order)
            self.set_option('active', dlg.active)

            self.update_actions()

    @Slot()
    def reset_window_layout(self):
        """Reset window layout to default."""
        answer = QMessageBox.warning(
            self,
            _("Warning"),
            _("Window layout will be reset to default settings: "
              "this affects window position, size and dockwidgets.\n"
              "Do you want to continue?"),
            QMessageBox.Yes | QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.setup_layout(default=True)

    @Slot()
    def toggle_previous_layout(self):
        self.toggle_layout('previous')

    @Slot()
    def toggle_next_layout(self):
        self.toggle_layout('next')

    def toggle_layout(self, direction='next'):
        """FIXME."""
        names = self.get_option('names')
        order = self.get_option('order')
        active = self.get_option('active')

        if len(active) == 0:
            return

        layout_index = ['default']
        for name in order:
            if name in active:
                layout_index.append(names.index(name))

        current_layout = self.current_quick_layout
        dic = {'next': 1, 'previous': -1}

        if current_layout is None:
            # Start from default
            current_layout = 'default'

        if current_layout in layout_index:
            current_index = layout_index.index(current_layout)
        else:
            current_index = 0

        new_index = (current_index + dic[direction]) % len(layout_index)

        self.quick_layout_switch(layout_index[new_index])

    def quick_layout_switch(self, index):
        """
        Switch to quick layout number *index*.

        Parameters
        ----------
        index: int
            FIXME:
        """
        section = 'quick_layouts'
        try:
            settings = self.load_window_settings('layout_{}/'.format(index),
                                                 section=section)
            (hexstate, window_size, prefs_dialog_size, pos, is_maximized,
             is_fullscreen) = settings

            # The defaults layouts will always be regenerated unless there was
            # an overwrite, either by rewriting with same name, or by deleting
            # and then creating a new one
            if hexstate is None:
                # The value for hexstate shouldn't be None for a custom saved
                # layout (ie, where the index is greater than the number of
                # defaults).  See spyder-ide/spyder#6202.
                if index != 'default' and index >= self.DEFAULT_LAYOUTS:
                    QMessageBox.critical(
                            self, _("Warning"),
                            _("Error opening the custom layout.  Please close"
                              " Spyder and try again.  If the issue persists,"
                              " then you must use 'Reset to Spyder default' "
                              "from the layout menu."))
                    return
                self.setup_default_layouts(index, settings)
        except cp.NoOptionError:
            QMessageBox.critical(self, _("Warning"),
                                 _("Quick switch layout #%s has not yet "
                                   "been defined.") % str(index))
            return

            # TODO: is there any real use in calling the previous layout
            # setting?
            # self.previous_layout_settings = self.get_window_settings()

        self.set_window_settings(*settings)
        self.current_quick_layout = index

        # make sure the flags are correctly set for visible panes
        for plugin in (self.widgetlist + self.thirdparty_plugins):
            action = plugin._toggle_view_action
            action.setChecked(plugin.dockwidget.isVisible())
