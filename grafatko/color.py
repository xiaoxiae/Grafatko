"""A class for constructing various colors, given the current canvas palette."""

from typing import *
from dataclasses import dataclass

from PyQt5.QtGui import *
from PyQt5.QtCore import *


def RGB(r: int, g: int, b: int):
    """The color from RGB."""
    return lambda palette: QColor.fromRgb(r, g, b)


def DEFAULT(palette: QPalette) -> QColor:
    """The default color, taken from the color of the text."""
    return palette.text().color()


def BACKGROUND(palette: QPalette) -> QColor:
    """The background color."""
    return palette.window().color()


def SELECTED(palette: QPalette) -> QColor:
    """The default color of selected nodes."""
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

    @classmethod
    def empty(cls):
        """Return an empty Brush."""
        return lambda _: Qt.NoBrush


class ColorAnimation:
    """A class for animating attribute transitions (color) when drawing the graph."""

    def __init__(
        self,
        start: Callable[[QPalette], QColor],
        end: Callable[[QPalette], QColor],
        duration: int = 200,
        update_period = 10,
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
