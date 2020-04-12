"""A class for constructing various colors, given the current canvas palette."""

from typing import *
from dataclasses import dataclass

from PyQt5.QtGui import *
from PyQt5.QtCore import *


def DEFAULT(palette: QPalette) -> QColor:
    """The default color, taken from the color of the text."""
    return palette.text().color()


def BACKGROUND(palette: QPalette) -> QColor:
    """The background color."""
    return palette.window().color()


def SELECTED(palette: QPalette) -> QColor:
    """The default color, taken from the color of the text."""
    return palette.alternateBase().color()


def lighter(color: Callable[[QPalette], QColor], coefficient: Union[float, int]):
    """A wrapper function that takes one of the functions above and makes it lighter."""
    return lambda palette: color(palette).lighter(coefficient)


def darker(color: Callable[[QPalette], QColor], coefficient: Union[float, int]):
    """A wrapper function that takes one of the functions above and makes it darker."""
    return lambda palette: color(palette).darker(coefficient)


@dataclass
class Colorable:
    color: Callable[[QPalette], QColor] = None


@dataclass
class Pen(Colorable):
    """A (wrapper) object storing a pen object."""

    style: Qt.PenStyle = Qt.SolidLine
    width: float = 0.1

    def __call__(self, palette: QPalette):
        return QPen(self.color(palette), self.width, self.style)


@dataclass
class Brush(Colorable):
    """A (wrapper) object storing a brush object."""

    style: Qt.BrushStyle = Qt.SolidPattern

    def __call__(self, palette: QPalette):
        return QBrush(self.color(palette), self.style)
