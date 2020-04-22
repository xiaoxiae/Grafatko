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

    def __call__(self, palette: QPalette) -> QColor:
        """Generated from the simple color function of the class."""
        return self.color_function(palette)


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


class ColorAnimation(ColorGenerating):
    """A class for animating attribute transitions (color) when drawing the graph."""

    default_duration = 1000

    def __init__(
        self,
        color_from: Color,
        color_to: Color,
        duration: int = None,
        parallel: bool = False,
    ):
        self.curve = QEasingCurve()  # the curve by which to interpolate

        # key values
        self.color_from = color_from
        self.color_to = color_to

        # whether the animation can be played in parallel or not
        self.parallel = parallel

        # for tracking whether the animation has started
        self.started = False

        self.duration = duration or self.__class__.default_duration
        self.timer = QElapsedTimer()  # the timer to track the animation

    def __call__(self, palette: QPalette):
        """Return the current interpolated value of the animation."""
        color_from = self.color_from(palette)
        color_to = self.color_to(palette)

        # get the curve value
        v = self.curve.valueForProgress(self.timer.elapsed() / self.duration)
        v = min(max(0, v), 1)  # restrict to a value from 0 to 1

        # return the interpolated color
        return QColor.fromRgb(
            color_from.red() * (1 - v) + color_to.red() * v,
            color_from.green() * (1 - v) + color_to.green() * v,
            color_from.blue() * (1 - v) + color_to.blue() * v,
        )

    @classmethod
    def set_default_duration(cls, value):
        cls.default_duration = value

    def is_parallel(self):
        """Return True if the animation is parallel, else False."""
        return self.parallel

    def start(self):
        """Start the animation."""
        self.timer.start()
        self.started = True

    def has_finished(self):
        """Return True if the animation finished, else False."""
        return self.has_started() and self.timer.elapsed() > self.duration

    def has_started(self):
        """Return True if the animation has started, else False."""
        return self.started
