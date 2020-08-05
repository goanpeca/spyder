# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Default layout definitions.
"""

# Third party imports
from qtpy.QtCore import QRect, QRectF, Qt
from qtpy.QtWidgets import (QApplication, QDockWidget, QGridLayout,
                            QMainWindow, QPlainTextEdit, QWidget)

# Local imports
from spyder.api.plugins import Plugins
from spyder.api.translations import get_translation
from spyder.plugins.layout.api import Locations, BaseGridLayoutType


# Localization
_ = get_translation("spyder")


class SpyderLayout(BaseGridLayoutType):
    ID = "spyder_default_layout"

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)

        self.add_area(
            [Plugins.Projects],
            row=0,
            column=0,
            row_span=2,
            visible=False,
        )
        self.add_area(
            [Plugins.Editor],
            row=0,
            column=1,
            row_span=2,
        )
        self.add_area(
            [Plugins.OutlineExplorer],
            row=0,
            column=2,
            row_span=2,
            visible=False,
        )
        self.add_area(
            [Plugins.Help, Plugins.VariableExplorer, Plugins.Plots,
             Plugins.OnlineHelp, Plugins.Explorer, Plugins.Find],
            row=0,
            column=3,
            default=True,
        )
        self.add_area(
            [Plugins.IPythonConsole, Plugins.History, Plugins.Console],
            row=1,
            column=3,
        )

        self.set_column_stretch(0, 1)
        self.set_column_stretch(1, 4)
        self.set_column_stretch(2, 1)
        self.set_column_stretch(3, 4)

    def get_name(self):
        return _("Spyder default")


class HorizontalSplitLayout(BaseGridLayoutType):
    ID = "horizontal_split_layout"

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)

        self.add_area(
            [Plugins.Editor],
            row=0,
            column=0,
        )
        self.add_area(
            [Locations.All],
            row=0,
            column=1,
            default=True,
        )

        self.set_column_stretch(0, 5)
        self.set_column_stretch(1, 4)

    def get_name(self):
        return _("Horizontal split")


class VerticalSplitLayout(BaseGridLayoutType):
    ID = "vertical_split_layout"

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)

        self.add_area(
            [Plugins.Editor],
            row=0,
            column=0,
        )
        self.add_area(
            [Locations.All],
            row=1,
            column=0,
            default=True,
        )

        self.set_row_stretch(0, 6)
        self.set_row_stretch(1, 4)

    def get_name(self):
        return _("Vertical split")


class RLayout(BaseGridLayoutType):
    ID = "r_layout"

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)

        self.add_area(
            [Plugins.Editor],
            row=0,
            column=0,
        )
        self.add_area(
            [Plugins.IPythonConsole, Plugins.Console],
            row=1,
            column=0,
        )
        self.add_area(
            [Plugins.VariableExplorer, Plugins.Plots, Plugins.History,
             Plugins.OutlineExplorer, Plugins.Find],
            row=0,
            column=1,
            default=True,
        )
        self.add_area(
            [Plugins.Explorer, Plugins.Projects, Plugins.Help,
             Plugins.OnlineHelp],
            row=1,
            column=1,
        )

    def get_name(self):
        return _("RStudio")


class MatlabLayout(BaseGridLayoutType):
    ID = "matlab_layout"

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)

        self.add_area(
            [Plugins.Explorer, Plugins.Projects],
            row=0,
            column=0,
        )
        self.add_area(
            [Plugins.OutlineExplorer],
            row=1,
            column=0,
        )
        self.add_area(
            [Plugins.Editor],
            row=0,
            column=1,
        )
        self.add_area(
            [Plugins.IPythonConsole, Plugins.Console],
            row=1,
            column=1,
        )
        self.add_area(
            [Plugins.VariableExplorer, Plugins.Plots, Plugins.Find],
            row=0,
            column=2,
            default=True,
        )
        self.add_area(
            [Plugins.History, Plugins.Help, Plugins.OnlineHelp],
            row=1,
            column=2,
        )

        self.set_column_stretch(0, 2)
        self.set_column_stretch(1, 3)
        self.set_column_stretch(2, 2)

        self.set_row_stretch(0, 3)
        self.set_row_stretch(1, 2)

    def get_name(self):
        return _("Matlab")


class VerticalSplitLayout2(BaseGridLayoutType):
    ID = "testing_layout"

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)

        self.add_area([Plugins.IPythonConsole], 0, 0, row_span=2)
        self.add_area([Plugins.Editor], 0, 1, col_span=2)
        self.add_area([Plugins.Explorer], 1, 1, default=True)
        self.add_area([Plugins.Help], 1, 2)
        self.add_area([Plugins.Console], 0, 3, row_span=2)
        self.add_area([Plugins.VariableExplorer], 2, 0, col_span=4, visible=False)

        self.set_column_stretch(0, 1)
        self.set_column_stretch(1, 4)
        self.set_column_stretch(2, 4)
        self.set_column_stretch(3, 1)

        self.set_row_stretch(0, 2)
        self.set_row_stretch(1, 2)
        self.set_row_stretch(2, 1)

    def get_name(self):
        return _("testing layout")


if __name__ == "__main__":
    for lay in [
            # SpyderLayout(None),
            # HorizontalSplitLayout(None),
            # VerticalSplitLayout(None),
            # RLayout(None),
            # MatlabLayout(None),
            VerticalSplitLayout2(None),
        ]:

        lay.show_example(show_hidden=True)
        lay._check_layout_validity()
        lay.set_main_window_layout()
