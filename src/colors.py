"""A class for constructing various colors, given the current canvas palette."""

from PyQt5.QtGui import *
from PyQt5.QtCore import *

from typing import *


def DEFAULT(palette: QPalette) -> QColor:
    """The default color, taken from the color of the text."""
    return palette.text().color()


def Brush(color: Callable[[QPalette], QColor], style: Qt.BrushStyle) -> QBrush:
    """A function that construct a brush from a color function and a style."""
    return lambda p: QBrush(color(p), style)


def Pen(color: Callable[[QPalette], QColor], style: Qt.PenStyle) -> QPen:
    """A function that construct a pen from a color function and a style."""
    return lambda p: QPen(color(p), style)
