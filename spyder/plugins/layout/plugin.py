# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Layout Plugin.
"""

import traceback

# Third party imports
from qtpy.QtCore import Signal, Qt, QByteArray, QSize, QPoint, Slot
from qtpy.QtWidgets import QDockWidget, QApplication

# Local imports
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.menus import ApplicationMenus, ViewMenuSections
from spyder.api.translations import get_translation
from spyder.config.base import STDERR
from spyder.plugins.layout.container import LayoutContainer
from spyder.plugins.layout.layouts import (HorizontalSplitLayout,
                                           MatlabLayout, RLayout,
                                           SpyderLayout, VerticalSplitLayout)
from spyder.py3compat import qbytearray_to_str  # FIXME:

# Localization
_ = get_translation("spyder")

# Constants
DEFAULT_LAYOUTS = 4


class Layout(SpyderPluginV2):
    """
    Layout manager plugin.
    """
    NAME = "layout"
    CONF_SECTION = "quick_layouts"
    OPTIONAL = [Plugins.All]
    CONF_FILE = False
    CONTAINER_CLASS = LayoutContainer

    # --- SpyderDockablePlugin API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _("Layout")

    def get_description(self):
        return _("Layout manager")

    def get_icon(self):
        return self.create_icon("history")  # FIXME:

    def register(self):
        container = self.get_container()
        self._last_plugin = None
        self._first_spyder_run = False
        self._state_before_maximizing = None

        # Register default layouts
        self.register_layout(self, SpyderLayout)
        self.register_layout(self, RLayout)
        self.register_layout(self, MatlabLayout)
        self.register_layout(self, HorizontalSplitLayout)
        self.register_layout(self, VerticalSplitLayout)

        # Add menu to View application menu
        layouts_menu = container._layouts_menu
        view_menu = self.get_application_menu(ApplicationMenus.View)
        self.add_item_to_application_menu(
            layouts_menu,
            view_menu,
            section=ViewMenuSections.Layout,
        )

    def before_mainwindow_visible(self):
        self.setup_layout(default=False)

    # --- Plubic API
    # ------------------------------------------------------------------------
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
        self.get_container().register_layout(parent_plugin, layout_type)

    def setup_layout(self, default=False):
        """Setup window layout"""
        prefix = 'window' + '/'
        settings = self.load_window_settings(prefix, default)
        hexstate = settings[0]

        self._first_spyder_run = False
        if hexstate is None:
            # First Spyder execution:
            self.main.setWindowState(Qt.WindowMaximized)
            self._first_spyder_run = True
            try:
                self.setup_default_layouts('default', settings)
            except Exception as error:
                print("\n\n")
                print(error)
                print("\n\n")

            # Now that the initial setup is done, copy the window settings,
            # except for the hexstate in the quick layouts sections for the
            # default layouts.
            # Order and name of the default layouts is found in config.py
            section = 'quick_layouts'
            # FIXME:
            get_func = self.get_conf_option_default if default else self.get_conf_option
            order = get_func(section, 'order')

            # restore the original defaults if reset layouts is called
            if default:
                self.set_conf_option(section, 'active', order)
                self.set_conf_option(section, 'order', order)
                self.set_conf_option(section, 'names', order)

            for index, _name, in enumerate(order):
                prefix = 'layout_{0}/'.format(index)
                self.save_current_window_settings(prefix, section,
                                                  none_state=True)

            # store the initial layout as the default in spyder
            prefix = 'layout_default/'
            section = 'quick_layouts'
            self.save_current_window_settings(prefix, section, none_state=True)
            self._current_quick_layout = 'default'

        self.set_window_settings(*settings)

        # Old API
        # for plugin in (self.widgetlist + self.thirdparty_plugins):
        #     try:
        #         plugin._initialize_plugin_in_mainwindow_layout()
        #     except AttributeError:
        #         pass
        #     except Exception as error:
        #         print("%s: %s" % (plugin, str(error)), file=STDERR)
        #         traceback.print_exc(file=STDERR)

    def setup_default_layouts(self, index, settings):
        """Setup default layouts when run for the first time."""
        self.main.setUpdatesEnabled(False)

        first_spyder_run = bool(self._first_spyder_run)  # Store copy

        if first_spyder_run:
            self.set_window_settings(*settings)
        else:
            if self._last_plugin:
                if self._last_plugin._ismaximized:
                    self.maximize_dockwidget(restore=True)

            if not (self.main.isMaximized() or self.maximized_flag):
                self.main.showMaximized()

            min_width = self.main.minimumWidth()
            max_width = self.main.maximumWidth()
            base_width = self.main.width()
            self.main.setFixedWidth(base_width)

        # IMPORTANT: order has to be the same as defined in the config file
        MATLAB, RSTUDIO, VERTICAL, HORIZONTAL = range(DEFAULT_LAYOUTS)

        # Define widgets locally
        editor = self.main.editor
        console_ipy = self.main.ipyconsole
        console_int = self.main.console
        outline = self.main.outlineexplorer
        explorer_project = self.main.projects
        explorer_file = self.main.explorer
        explorer_variable = self.main.variableexplorer
        plots = self.main.plots
        history = self.main.historylog
        finder = self.main.findinfiles
        help_plugin = self.main.help
        helper = self.main.onlinehelp
        plugins = self.main.thirdparty_plugins

        # Stored for tests
        # FIXME!
        global_hidden_widgets = [finder, console_int, explorer_project,
                                 helper] + plugins
        global_hidden_toolbars = [self.main.source_toolbar, self.main.edit_toolbar,
                                  self.main.search_toolbar]
        # Layout definition
        # --------------------------------------------------------------------
        # Layouts are organized by columns, each column is organized by rows.
        # Widths have to accumulate to 100 (except if hidden), height per
        # column has to accumulate to 100 as well

        # Spyder Default Initial Layout
        s_layout = {
            'widgets': [
                # Column 0
                [[explorer_project]],
                # Column 1
                [[editor]],
                # Column 2
                [[outline]],
                # Column 3
                [[help_plugin, explorer_variable, plots,     # Row 0
                  helper, explorer_file, finder] + plugins,
                 [console_int, console_ipy, history]]        # Row 1
                ],
            'width fraction': [15,            # Column 0 width
                               45,            # Column 1 width
                                5,            # Column 2 width
                               45],           # Column 3 width
            'height fraction': [[100],          # Column 0, row heights
                                [100],          # Column 1, row heights
                                [100],          # Column 2, row heights
                                [46, 54]],  # Column 3, row heights
            'hidden widgets': [outline] + global_hidden_widgets,
            'hidden toolbars': [],
        }

        # RStudio
        r_layout = {
            'widgets': [
                # column 0
                [[editor],                            # Row 0
                 [console_ipy, console_int]],         # Row 1
                # column 1
                [[explorer_variable, plots, history,  # Row 0
                  outline, finder] + plugins,
                 [explorer_file, explorer_project,    # Row 1
                  help_plugin, helper]]
                ],
            'width fraction': [55,            # Column 0 width
                               45],           # Column 1 width
            'height fraction': [[55, 45],   # Column 0, row heights
                                [55, 45]],  # Column 1, row heights
            'hidden widgets': [outline] + global_hidden_widgets,
            'hidden toolbars': [],
        }

        # Matlab
        m_layout = {
            'widgets': [
                # column 0
                [[explorer_file, explorer_project],
                 [outline]],
                # column 1
                [[editor],
                 [console_ipy, console_int]],
                # column 2
                [[explorer_variable, plots, finder] + plugins,
                 [history, help_plugin, helper]]
                ],
            'width fraction': [10,            # Column 0 width
                               45,            # Column 1 width
                               45],           # Column 2 width
            'height fraction': [[55, 45],   # Column 0, row heights
                                [55, 45],   # Column 1, row heights
                                [55, 45]],  # Column 2, row heights
            'hidden widgets': global_hidden_widgets,
            'hidden toolbars': [],
        }

        # Vertically split
        v_layout = {
            'widgets': [
                # column 0
                [[editor],                                  # Row 0
                 [console_ipy, console_int, explorer_file,  # Row 1
                  explorer_project, help_plugin, explorer_variable, plots,
                  history, outline, finder, helper] + plugins]
                ],
            'width fraction': [100],            # Column 0 width
            'height fraction': [[55, 45]],  # Column 0, row heights
            'hidden widgets': [outline] + global_hidden_widgets,
            'hidden toolbars': [],
        }

        # Horizontally split
        h_layout = {
            'widgets': [
                # column 0
                [[editor]],                                 # Row 0
                # column 1
                [[console_ipy, console_int, explorer_file,  # Row 0
                  explorer_project, help_plugin, explorer_variable, plots,
                  history, outline, finder, helper] + plugins]
                ],
            'width fraction': [55,      # Column 0 width
                               45],     # Column 1 width
            'height fraction': [[100],    # Column 0, row heights
                                [100]],   # Column 1, row heights
            'hidden widgets': [outline] + global_hidden_widgets,
            'hidden toolbars': []
        }

        # Layout selection
        layouts = {
            'default': s_layout,
            RSTUDIO: r_layout,
            MATLAB: m_layout,
            VERTICAL: v_layout,
            HORIZONTAL: h_layout,
        }

        layout = layouts[index]

        # Remove None from widgets layout
        widgets_layout = layout['widgets']
        widgets_layout_clean = []
        for column in widgets_layout:
            clean_col = []
            for row in column:
                clean_row = [w for w in row if w is not None]
                if clean_row:
                    clean_col.append(clean_row)
            if clean_col:
                widgets_layout_clean.append(clean_col)

        # Flatten widgets list
        widgets = []
        for column in widgets_layout_clean:
            for row in column:
                for widget in row:
                    widgets.append(widget)

        # We use both directions to ensure proper update when moving from
        # 'Horizontal Split' to 'Spyder Default'
        # This also seems to help on random cases where the display seems
        # 'empty'
        for direction in (Qt.Vertical, Qt.Horizontal):
            # Arrange the widgets in one direction
            for idx in range(len(widgets) - 1):
                first, second = widgets[idx], widgets[idx+1]
                if first is not None and second is not None:
                    self.main.splitDockWidget(
                        first.dockwidget,
                        second.dockwidget,
                        direction,
                    )

        # Arrange the widgets in the other direction
        for column in widgets_layout_clean:
            for idx in range(len(column) - 1):
                first_row, second_row = column[idx], column[idx+1]
                self.main.splitDockWidget(
                    first_row[0].dockwidget,
                    second_row[0].dockwidget,
                    Qt.Vertical,
                )

        # Tabify
        for column in widgets_layout_clean:
            for row in column:
                for idx in range(len(row) - 1):
                    first, second = row[idx], row[idx+1]
                    self.tabify_plugins(first, second)

                # Raise front widget per row
                row[0].dockwidget.show()
                row[0].dockwidget.raise_()

        # Set dockwidget widths
        width_fractions = layout['width fraction']
        if len(width_fractions) > 1:
            _widgets = [col[0][0].dockwidget for col in widgets_layout]
            self.main.resizeDocks(_widgets, width_fractions, Qt.Horizontal)

        # Set dockwidget heights
        height_fractions = layout['height fraction']
        for idx, column in enumerate(widgets_layout_clean):
            if len(column) > 1:
                _widgets = [row[0].dockwidget for row in column]
                self.main.resizeDocks(_widgets, height_fractions[idx], Qt.Vertical)

        # Hide toolbars
        hidden_toolbars = global_hidden_toolbars + layout['hidden toolbars']
        for toolbar in hidden_toolbars:
            if toolbar is not None:
                toolbar.close()

        # Hide widgets
        hidden_widgets = layout['hidden widgets']
        for widget in hidden_widgets:
            if widget is not None:
                widget.dockwidget.close()

        if first_spyder_run:
            self._first_spyder_run = False
        else:
            self.main.setMinimumWidth(min_width)
            self.main.setMaximumWidth(max_width)

            if not (self.main.isMaximized() or self.maximized_flag):
                self.main.showMaximized()

        self.main.setUpdatesEnabled(True)
        # self.sig_layout_setup_ready.emit(layout)

        return layout

    def load_window_settings(self, prefix, default=False, section='main'):
        """
        Load window layout settings from userconfig-based configuration with
        *prefix*, under *section* default: if True, do not restore inner
        layout.
        """
        #FIXME:
        # get_func = self.get_conf_option_default if default else self.get_conf_option
        get_func = self.get_conf_option
        window_size = get_func(prefix + 'size', section=section)
        prefs_dialog_size = get_func(prefix + 'prefs_dialog_size', section=section)

        if default:
            hexstate = None
        else:
            # FIXME:
            try:
                hexstate = get_func(prefix + 'state', section=section)
            except Exception:
                hexstate = None

        pos = get_func(prefix + 'position', section=section)

        # It's necessary to verify if the window/position value is valid
        # with the current screen. See spyder-ide/spyder#3748.
        width = pos[0]
        height = pos[1]
        screen_shape = QApplication.desktop().geometry()
        current_width = screen_shape.width()
        current_height = screen_shape.height()
        if current_width < width or current_height < height:
            pos = self.get_conf_option(prefix + 'position', section)

        is_maximized =  get_func(prefix + 'is_maximized', section=section)
        is_fullscreen = get_func(prefix + 'is_fullscreen', section=section)
        return (hexstate, window_size, prefs_dialog_size, pos, is_maximized,
                is_fullscreen)

    def get_window_settings(self):
        """
        Return current window settings.

        Symetric to the 'set_window_settings' setter.
        """
        # FIXME: Window size in main window is update on resize
        window_size = (self.window_size.width(), self.window_size.height())

        is_fullscreen = self.main.isFullScreen()
        if is_fullscreen:
            is_maximized = self.maximized_flag
        else:
            is_maximized = self.main.isMaximized()

        pos = (self.window_position.x(), self.window_position.y())
        prefs_dialog_size = (self.prefs_dialog_size.width(),
                             self.prefs_dialog_size.height())

        hexstate = qbytearray_to_str(self.main.saveState())
        return (hexstate, window_size, prefs_dialog_size, pos, is_maximized,
                is_fullscreen)

    def set_window_settings(self, hexstate, window_size, prefs_dialog_size,
                            pos, is_maximized, is_fullscreen):
        """
        Set window settings Symetric to the 'get_window_settings' accessor.
        """
        self.main.setUpdatesEnabled(False)
        self.window_size = QSize(window_size[0], window_size[1]) # width,height
        self.prefs_dialog_size = QSize(prefs_dialog_size[0],
                                       prefs_dialog_size[1]) # width,height
        self.window_position = QPoint(pos[0], pos[1]) # x,y
        self.main.setWindowState(Qt.WindowNoState)
        self.main.resize(self.window_size)
        self.main.move(self.window_position)

        # Window layout
        if hexstate:
            self.main.restoreState(
                QByteArray().fromHex(str(hexstate).encode('utf-8')))

            # FIXME:
            # Workaround for spyder-ide/spyder#880.
            # QDockWidget objects are not painted if restored as floating
            # windows, so we must dock them before showing the mainwindow.
            for widget in self.children():
                if isinstance(widget, QDockWidget) and widget.isFloating():
                    self.floating_dockwidgets.append(widget)
                    widget.setFloating(False)

        # Is fullscreen?
        if is_fullscreen:
            self.main.setWindowState(Qt.WindowFullScreen)

        # FIXME:
        # self.__update_fullscreen_action()

        # Is maximized?
        if is_fullscreen:
            self.maximized_flag = is_maximized
        elif is_maximized:
            self.main.setWindowState(Qt.WindowMaximized)

        self.main.setUpdatesEnabled(True)

    def save_current_window_settings(self, prefix, section='main',
                                     none_state=False):
        """
        Save current window settings with *prefix* in the userconfig-based configuration, under *section*.
        """
        win_size = self.window_size
        prefs_size = self.prefs_dialog_size

        self.set_conf_option(
            prefix + 'size',
            (win_size.width(), win_size.height()),
            section=section,
        )
        self.set_conf_option(
            prefix + 'prefs_dialog_size',
            (prefs_size.width(), prefs_size.height()),
            section=section,
        )
        self.set_conf_option(
            prefix + 'is_maximized',
            self.isMaximized(),
            section=section,
        )
        self.set_conf_option(
            prefix + 'is_fullscreen',
            self.isFullScreen(),
            section=section,
        )

        pos = self.window_position
        self.set_conf_option(
            prefix + 'position',
            (pos.x(), pos.y()),
            section=section,
        )

        # FIXME: Bring this over
        self.maximize_dockwidget(restore=True)# Restore non-maximized layout

        if none_state:
            self.set_conf_option(
                prefix + 'state',
                None,
                section=section,
            )
        else:
            qba = self.main.saveState()
            self.set_conf_option(
                prefix + 'state',
                qbytearray_to_str(qba),
                section=section,
            )

        self.set_conf_option(
            prefix + 'statusbar',
            not self.main.statusBar().isHidden(),
            section=section,
        )

    def tabify_plugins(self, first, second):
        """Tabify plugin dockwigdets"""
        self.main.tabifyDockWidget(first.dockwidget, second.dockwidget)

    @Slot()
    @Slot(bool)
    def maximize_dockwidget(self, restore=False):
        """Shortcut: Ctrl+Alt+Shift+M
        First call: maximize current dockwidget
        Second call (or restore=True): restore original window layout"""
        return

        # FIXME:
        if self._state_before_maximizing is None:
            if restore:
                return

            # Select plugin to maximize
            self._state_before_maximizing = self.saveState()
            focus_widget = QApplication.focusWidget()

            for plugin in (self.widgetlist + self.thirdparty_plugins):
                plugin.dockwidget.hide()

                try:
                    # New API
                    if plugin.get_widget().isAncestorOf(focus_widget):
                        self._last_plugin = plugin
                except Exception:
                    # Old API
                    if plugin.isAncestorOf(focus_widget):
                        self._last_plugin = plugin

            # Only plugins that have a dockwidget are part of widgetlist,
            # so last_plugin can be None after the above "for" cycle.
            # For example, this happens if, after Spyder has started, focus
            # is set to the Working directory toolbar (which doesn't have
            # a dockwidget) and then you press the Maximize button
            if self._last_plugin is None:
                # Using the Editor as default plugin to maximize
                self._last_plugin = self.editor

            # Maximize last_plugin
            self._last_plugin.dockwidget.toggleViewAction().setDisabled(True)
            try:
                # New API
                self.main.setCentralWidget(self._last_plugin.get_widget())
            except AttributeError:
                # Old API
                self.main.setCentralWidget(self._last_plugin)

            self._last_plugin._ismaximized = True

            # Workaround to solve an issue with editor's outline explorer:
            # (otherwise the whole plugin is hidden and so is the outline explorer
            #  and the latter won't be refreshed if not visible)
            try:
                # New API
                self._last_plugin.get_widget().show()
                self._last_plugin.change_visibility(True)
            except AttributeError:
                # Old API
                self._last_plugin.show()
                self._last_plugin._visibility_changed(True)

            if self._last_plugin is self.editor:
                # Automatically show the outline if the editor was maximized:
                self.main.addDockWidget(Qt.RightDockWidgetArea,
                                   self.outlineexplorer.dockwidget)
                # FIXME:
                self.outlineexplorer.dockwidget.show()
        else:
            # Restore original layout (before maximizing current dockwidget)
            try:
                # New API
                self._last_plugin.dockwidget.setWidget(
                    self._last_plugin.get_widget())
            except AttributeError:
                # Old API
                self._last_plugin.dockwidget.setWidget(self._last_plugin)

            self._last_plugin.dockwidget.toggleViewAction().setEnabled(True)
            self.main.setCentralWidget(None)

            try:
                # New API
                self._last_plugin.get_widget().is_maximized = False
            except AttributeError:
                # Old API
                self._last_plugin._ismaximized = False

            self.main.restoreState(self._state_before_maximizing)
            self._state_before_maximizing = None
            try:
                # New API
                self._last_plugin.get_widget().get_focus_widget().setFocus()
            except AttributeError:
                # Old API
                self._last_plugin.get_focus_widget().setFocus()

        self._update_maximize_action()

    def _update_maximize_action(self):
        pass
        # if self._state_before_maximizing is None:
        #     text = _("Maximize current pane")
        #     tip = _("Maximize current pane")
        #     icon = ima.icon('maximize')
        # else:
        #     text = _("Restore current pane")
        #     tip = _("Restore pane to its original size")
        #     icon = ima.icon('unmaximize')

        # # FIXME:
        # self.maximize_action.setText(text)
        # self.maximize_action.setIcon(icon)
        # self.maximize_action.setToolTip(tip)
