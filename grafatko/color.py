"""A class for constructing various colors, given the current canvas palette."""

from __future__ import annotations
from typing import *

from dataclasses import dataclass

from abc import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ColorGenerating(ABC):
    """A class that when called with a QPalette produces a QColor. Done to be
    application theme independent"""

    @abstractmethod
    def __call__(self, palette: QPalette) -> QColor:
        """Generate the color, given the palette and the color function."""
        pass


class Color(ColorGenerating):
    """A class for generating QColors, given a QPalette."""

    def __init__(self, color_function: Callable[[QPalette], QColor]):
        self.color_function = color_function

    @classmethod
    def text(cls) -> Color:
        """The text color of the palette"""
        return Color(lambda palette: palette.text().color())

    @classmethod
    def background(cls) -> Color:
        """The background color of the palette."""
        return Color(lambda palette: palette.window().color())

    @classmethod
    def red(cls) -> Color:
        return Color(lambda _: QColor.fromRgb(255, 0, 0))

    @classmethod
    def green(cls) -> Color:
        return Color(lambda _: QColor.fromRgb(0, 255, 0))

    @classmethod
    def blue(cls) -> Color:
        return Color(lambda _: QColor.fromRgb(0, 0, 255))

    @classmethod
    def selected(cls) -> Color:
        """The text color of things that are selected."""
        return Color(lambda palette: palette.alternateBase().color())

    def lighter(self, coefficient: float) -> Color:
        """Return a Color object that is lighter than the current one by a coefficient."""
        return Color(lambda palette: self.color_function(palette).lighter(coefficient))

    def darker(self, coefficient: float) -> Color:
        """Return a Color object that is darker than the current one by a coefficient."""
        return Color(lambda palette: self.color_function(palette).darker(coefficient))

    @classmethod
    def __contrast(cls, color: QColor) -> QColor:
        average = 255 - (color.red() + color.green() + color.blue()) / 3
        return QColor.fromRgb(average, average, average)

    @classmethod
    def contrast(cls, color: Color) -> Color:
        """Return a Color object returning a color from white to black that is in
        contrast to the given color."""
        return Color(lambda palette: cls.__contrast(color(palette)))

    def __call__(self, palette: QPalette) -> QColor:
        """Generated from the simple color function of the class."""
        return self.color_function(palette)


@dataclass
class Colorable:
    """Something that can be colored."""

    color: ColorGenerating = Color.text()

    def set_color(self, color: ColorGenerating):
        self.color = color

    def get_color(self) -> ColorGenerating:
        return self.color


@dataclass
class Pen(Colorable):
    """A (wrapper) object storing a pen object."""

    style: Qt.PenStyle = Qt.SolidLine
    width: float = 0.1

    def __call__(self, palette: QPalette):
        return QPen(self.get_color()(palette), self.width, self.style)


@dataclass
class Brush(Colorable):
    """A (wrapper) object storing a brush object."""

    style: Qt.BrushStyle = Qt.SolidPattern

    def __call__(self, palette: QPalette):
        return QBrush(self.get_color()(palette), self.style)

    @classmethod
    def empty(cls):
        """Return an empty Brush."""
        return lambda _: Qt.NoBrush
