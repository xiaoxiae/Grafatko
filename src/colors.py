"""A class for constructing various colors, given the current canvas palette."""

from PyQt5.QtGui import *
from PyQt5.QtCore import *

from typing import *

from dataclasses import dataclass


def DEFAULT(palette: QPalette) -> QColor:
    """The default color, taken from the color of the text."""
    return palette.text().color()


def SELECTED(palette: QPalette) -> QColor:
    """The default color, taken from the color of the text."""
    return palette.alternateBase().color()


@dataclass
class Colorable:
    color: Callable[[QPalette], QColor] = None


@dataclass
class Pen(Colorable):
    """A (wrapper) object storing a pen object."""

    style: Qt.PenStyle = None
    width: float = 0.3

    def __call__(self, palette: QPalette):
        return QPen(self.color(palette), self.width, self.style)


@dataclass
class Brush(Colorable):
    """A (wrapper) object storing a brush object."""

    style: Qt.BrushStyle = None

    def __call__(self, palette: QPalette):
        return QBrush(self.color(palette), self.style)
