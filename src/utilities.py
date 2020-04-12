"""A class containing useful utility classes."""

from __future__ import annotations
from typing import *
from math import sqrt, sin, cos

from dataclasses import *


class Vector:
    """A Python implementation of a vector class and some of its operations."""

    values = None

    def __init__(self, *args):
        self.values = list(args)

    def __str__(self):
        """String representation of a vector is its components surrounded by < and >."""
        return f"<{str(self.values)[1:-1]}>"

    __repr__ = __str__

    def __len__(self):
        """Defines the length of the vector as the number of its components."""
        return len(self.values)

    def __hash__(self):
        """Defines the hash of the vector as a hash of a tuple with its components."""
        return hash(tuple(self))

    def __eq__(self, other):
        """Defines vector equality as the equality of all of its components."""
        return self.values == other.values

    def __setitem__(self, i, value):
        """Sets the i-th vector component to the specified value."""
        self.values[i] = value

    def __getitem__(self, i):
        """Either returns a new vector when sliced, or the i-th vector component."""
        if type(i) == slice:
            return Vector(*self.values[i])
        else:
            return self.values[i]

    def __delitem__(self, i):
        """Deletes the i-th component of the vector."""
        del self.values[i]

    def __neg__(self):
        """Defines vector negation as the negation of all of its components."""
        return Vector(*iter(-component for component in self))

    def __add__(self, other):
        """Defines vector addition as the addition of each of their components."""
        return Vector(*iter(u + v for u, v in zip(self, other)))

    __iadd__ = __add__

    def __sub__(self, other):
        """Defines vector subtraction as the subtraction of each of its components."""
        return Vector(*iter(u - v for u, v in zip(self, other)))

    __isub__ = __sub__

    def __mul__(self, other):
        """Defines scalar and dot multiplication of a vector."""
        if type(other) == int or type(other) == float:
            # scalar multiplication
            return Vector(*iter(component * other for component in self))
        else:
            # dot multiplication
            return sum(u * v for u, v in zip(self, other))

    __rmul__ = __imul__ = __mul__

    def __truediv__(self, other):
        """Defines vector division by a scalar."""
        return Vector(*iter(component / other for component in self))

    def __floordiv__(self, other):
        """Defines floor vector division by a scalar."""
        return Vector(*iter(component // other for component in self))

    def __matmul__(self, other):
        """Defines cross multiplication of a vector."""
        return Vector(
            self[1] * other[2] - self[2] * other[1],
            self[2] * other[0] - self[0] * other[2],
            self[0] * other[1] - self[1] * other[0],
        )

    __imatmul__ = __matmul__

    def __mod__(self, other):
        """Defines vector mod as the mod of its components."""
        return Vector(*iter(component % other for component in self))

    def magnitude(self):
        """Returns the magnitude of the vector."""
        return sqrt(sum(component ** 2 for component in self))

    def rotated(self, angle: float, point: Vector = None):
        """Returns this vector rotated by an angle (in radians) around a certain point."""
        if point is None:
            point = Vector(0, 0)

        return self.__rotated(self - point, angle) + point

    def __rotated(self, vector: Vector, angle: float):
        """Returns a vector rotated by an angle (in radians)."""
        return Vector(
            vector[0] * cos(angle) - vector[1] * sin(angle),
            vector[0] * sin(angle) + vector[1] * cos(angle),
        )

    def unit(self):
        """Returns a unit vector with the same direction as this vector."""
        return self / self.magnitude()

    def abs(self):
        """Returns a vector with absolute values of the components of this vector."""
        return Vector(*iter(abs(component) for component in self))

    def distance(self, other: Vector):
        """Returns the distance of two Vectors in space."""
        return sqrt(sum(map(lambda x: sum(x) ** 2, zip(self, -other))))

    def repeat(self, n):
        """Performs sequence repetition on the vector (n times)."""
        return Vector(*self.values * n)

    @classmethod
    def sum(cls, l: List[Vector]):
        """Return the sum of the given vectors."""
        return sum(l[1:], l[0])

    @classmethod
    def average(cls, l: List[Vector]):
        """Return the average of the given vectors."""
        return Vector.sum(l) / len(l)


@dataclass
class Transformation:
    """A class for working with the current transformation of the canvas."""

    canvas: QWidget  # get the widget so we can calculate the current width and height

    # initial scale and transformation
    scale: float = 20
    translation: float = Vector(0, 0)

    # how smooth to make the centering of the transformation
    center_smoothness: Final = 0.3

    def transform_painter(self, painter: QPainter):
        """Translate the painter according to the current canvas state."""
        painter.translate(*self.translation)
        painter.scale(self.scale, self.scale)

    def apply(self, point: Vector):
        """Apply the current canvas transformation on the point."""
        return (point - self.translation) / self.scale

    def inverse(self, point: Vector):
        """The inverse of apply."""
        return point * self.scale + self.translation

    def center(self, point: Vector):
        """Center the transformation on the given point."""
        middle = self.apply(Vector(self.canvas.width(), self.canvas.height()) / 2)
        self.translation = self.inverse((middle - point) * self.center_smoothness)

    def translate(self, delta: Vector):
        """Translate the transformation by the vector delta delta."""
        self.translation += delta * self.scale

    def zoom(self, position: Vector, delta: float):
        """Zoom in/out."""
        # adjust the scale
        previous_scale = self.scale
        self.scale *= 2 ** delta  # scale smoothly

        # adjust translation so the x and y of the mouse stay in the same spot
        self.translation -= position * (self.scale - previous_scale)
