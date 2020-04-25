from __future__ import annotations
from typing import *

from abc import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from grafatko.color import *


class Animation:
    """A base class for all animations in the project. Returns values from 0 to 1
    when started and called."""

    default_duration = 1000

    def __init__(self, duration: int = None, parallel: bool = False):
        self.curve = QEasingCurve()  # the curve by which to interpolate

        # whether the animation can be played in parallel or not
        self.parallel = parallel

        # for tracking whether the animation has started
        self.started = False

        # for tracking whether the animation is paused
        self.paused = False
        self.paused_time = 0

        # either the provided duration or the class default
        self.duration = duration or self.__class__.default_duration
        self.timer = QElapsedTimer()  # the timer to track the animation

    def __call__(self) -> int:
        """Return the current interpolated color."""
        # get the time -- start with the paused value and add elapsed, if we're not paused
        time = self.paused_time + (0 if self.is_paused() else self.timer.elapsed())

        # get the curve value
        v = self.curve.valueForProgress(time / self.duration)

        # return it, clamped (from 0 to 1, inclusive)
        return min(max(0, v), 1)

    @classmethod
    def set_default_duration(cls, value):
        """Set the default duration of animations being created."""
        cls.default_duration = value

    def is_parallel(self) -> bool:
        """Return True if the animation is parallel, else False."""
        return self.parallel

    def start(self):
        """Start the animation."""
        self.timer.start()
        self.started = True

    def pause(self):
        """Pause the animation (if it's started and not paused already)."""
        if self.has_started() and not self.is_paused():
            self.paused = True
            self.paused_time = self.timer.elapsed()

    def is_paused(self) -> bool:
        """Return True if the animation is paused, else False."""
        return self.paused

    def resume(self):
        """Resume the animation (if it's paused)."""
        if self.has_started() and self.is_paused():
            self.paused = False
            self.timer.restart()

    def has_finished(self) -> bool:
        """Return True if the animation has finished, else False. It has to have
        started, the time must have elapsed and it mustn't be currently paused."""
        return (
            self.has_started()
            and (self.paused_time + self.timer.elapsed()) > self.duration
            and not self.is_paused()
        )

    def has_started(self) -> bool:
        """Return True if the animation has started, else False."""
        return self.started


class ColorAnimation(Animation, ColorGenerating):
    """A class for animating attribute transitions (color) when drawing the graph."""

    default_duration = 1000

    def __init__(self, color_from: Color, color_to: Color, *args, **kwargs):
        self.color_from = color_from
        self.color_to = color_to

        super().__init__(*args, **kwargs)

    def __call__(self, palette: QPalette) -> QColor:
        """Return the current interpolated color."""
        color_from = self.color_from(palette)
        color_to = self.color_to(palette)

        v = super().__call__()

        # return the interpolated color
        return QColor.fromRgb(
            color_from.red() * (1 - v) + color_to.red() * v,
            color_from.green() * (1 - v) + color_to.green() * v,
            color_from.blue() * (1 - v) + color_to.blue() * v,
        )

    def get_start_value(self):
        """Return the start value of the animation."""
        return self.color_from

    def get_end_value(self):
        """Return the end value of the animation."""
        return self.color_to
