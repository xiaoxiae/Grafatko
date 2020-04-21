"""A class for constructing various colors, given the current canvas palette."""

from __future__ import annotations
from typing import *
from dataclasses import dataclass

from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Color:
    """A class for generating QColors, given a QPalette. Done to be application theme
    independent."""

    def __init__(self, color_function: Callable[[QPalette], QColor]):
        self.color_function = color_function

    @classmethod
    def text(self) -> Color:
        """The text color of the palette"""
        return Color(lambda palette: palette.text().color())

    @classmethod
    def background(self) -> Color:
        """The background color of the palette."""
        return Color(lambda palette: palette.window().color())

    @classmethod
    def selected(self) -> Color:
        """The text color of things that are selected."""
        return Color(lambda palette: palette.alternateBase().color())

    def __call__(self, palette: QPalette) -> QColor:
        """Generate the color, given the palette and the color function."""
        return self.color_function(palette)

    def lighter(self, coefficient: float) -> Color:
        """Return a Color object that is lighter than the current one by a coefficient."""
        return Color(lambda palette: self.color_function(palette).lighter(coefficient))

    def darker(self, coefficient: float) -> Color:
        """Return a Color object that is darker than the current one by a coefficient."""
        return Color(lambda palette: self.color_function(palette).darker(coefficient))


@dataclass
class Colorable:
    """Something that can be colored."""

    color: Color = Color.text()

    def set_color(self, color: Color):
        self.color = color

    def get_color(self) -> Color:
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


class ColorAnimation:
    """A class for animating attribute transitions (color) when drawing the graph."""

    def __init__(
        self, start: Color, end: Color, duration: int = 200, update_period=10,
    ):
        # the timer to track the animation
        self.timer = QTimer()

        # key values
        self.start = start
        self.end = end

        # whether the animation can be played in parallel or not
        self.parallel = parallel

        # for tracking whether the animation has finished
        self.finished = False
        self.timer.timeout.connect(self.__finished())

        self.timer.start(duration)

    def get_value(self, palette: QPalette):
        """Return the current interpolated value of the animation."""
        QVariantAnimation().interpolated(
            self.start(palette),
            self.end(palette),
            self.timer.remainingTime() / self.interval(),
        )

    def __finished(self):
        """Internal callback function for setting self.finished."""
        self.finished = True

    def has_finished(self):
        """Return True if the animation finished, else False."""
        return self.finished
