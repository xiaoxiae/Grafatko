"""A class for working with graphs."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, List, Union

from graph import *
from utilities import *

from abc import *

from PyQt5.QtGui import *


class Drawable(ABC):
    """Something that can be drawn on the PyQt5 canvas."""

    @abstractmethod
    def draw(self, painter: QPainter):
        """A method that draws the object on the canvas."""
        pass


class DrawableNode(Drawable, Node):
    def __init__(self, position, *arg):
        self.position: Vector = position

        super().__init__(*arg)

        self.forces: List[Vector] = []

        # for drawing the outgoing vertices
        self.adjacent_pen: Dict[Node, QPen] = field(default_factory=dict)

        # for drawing the node itself
        self.pen: QPen = None
        self.brush: QBrush = None

    def get_adjacent(self) -> Dict[Node, Tuple[Union[int, float], Color]]:
        """Returns nodes adjacent to the node and the vertex colors that they have."""
        return self.adjacent

    def get_position(self) -> Vector:
        """Return the position of the node."""
        return self.position

    def set_position(self, position: Vector):
        """Return the position of the node."""
        self.position = position

    def add_force(self, force: Vector):
        """Adds a force that is acting upon the node to the force list."""
        self.forces.append(force)

    def evaluate_forces(self):
        """Evaluates all of the forces acting upon the node and moves it accordingly."""
        while len(self.forces) != 0:
            self.position += self.forces.pop()

    def draw():
        pass


class DrawableGraph(Drawable, Graph):
    def draw(self):
        # draw each node
        # draw each vertex
        pass
