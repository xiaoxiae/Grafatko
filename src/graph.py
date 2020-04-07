"""A wrapper for working with graphs that can be drawn."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import *


# QT
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# UTILITIES
from utilities import *
from ast import literal_eval
from collections import defaultdict
from math import sqrt, cos, sin, radians, pi
from abc import *


# COLORS
from colors import *


@dataclass(eq=False)
class Node:
    """A class for working with of nodes in a graph."""

    label: str = None
    adjacent: Dict[Node, Union[int, float]] = field(default_factory=dict)

    def get_adjacent(self) -> Dict[Node, Union[int, float]]:
        """Returns nodes adjacent to the node."""
        return self.adjacent

    def get_label(self) -> Union[str, None]:
        """Returns the label of the node (or None if has none)."""
        return self.label

    def set_label(self, label: Union[str, None]):
        """Sets the label of the node to the specified value."""
        self.label = label


@dataclass
class Graph:
    """A class for working with graphs."""

    directed: bool = False
    weighted: bool = False

    nodes: List[Node] = field(default_factory=list)

    # a component array that gets recalculated on each destructive graph operation
    # takes O(n^2) to rebuild, but O(1) to check components, so it's better for us
    # TODO: make rebuilding faster (I was too lazy before)
    components: Dict[Node, int] = field(default_factory=defaultdict)

    def recalculate_components(function):
        """A decorator for rebuilding the components of the graph."""

        def wrapper(self, *args, **kwargs):
            # first add/remove vertex/node/...
            function(self, *args, **kwargs)

            self.components = []

            for node in self.nodes:
                # the current set of nodes that we know are reachable from one another
                component = set([node] + list(node.get_adjacent()))

                i = 0
                while i < len(self.components):
                    if len(self.components[i].intersection(component)) != 0:
                        component |= self.components.pop(i)
                    else:
                        i += 1

                self.components.append(component)

        return wrapper

    def weakly_connected(self, n1: Node, n2: Node):
        """Return True if the nodes are weakly connected."""
        for component in self.components:
            a = n1 in component
            b = n2 in component

            if a and b:
                return True
            elif a or b:
                return False

    def get_directed(self) -> bool:
        """Returns True if the graph is directed, else False."""
        return self.directed

    def set_directed(self, directed: bool):
        """Sets, whether the graph is directed or not."""
        # if we're converting to undirected, make all current vertices go both ways
        if not directed and not self.directed:
            for node in self.nodes:
                for neighbour in node.adjacent:
                    if node is neighbour:
                        # no loops allowed!
                        self.remove_vertex(node, neighbour)
                    else:
                        self.add_vertex(neighbour, node)

        self.directed = directed

    def get_weighted(self) -> bool:
        """Returns True if the graph is weighted and False otherwise."""
        return self.weighted

    def set_weighted(self, value: bool):
        """Sets, whether the graph is weighted or not."""
        self.weighted = value

    def get_weight(self, n1: Node, n2: Node) -> Union[Union[int, float], None]:
        """Returns the weight of the specified vertex (and None if they're not connected)."""
        return (
            None
            if not self.is_vertex(n1, n2)
            else self.nodes[self.nodes.index(n1)].adjacent[n2]
        )

    def get_nodes(self) -> List[Node]:
        """Returns a list of nodes of the graph."""
        return self.nodes

    @recalculate_components
    def add_node(self, node: Node):
        """Adds a new node to the graph."""
        self.nodes.append(node)

    @recalculate_components
    def remove_node(self, n: Node):
        """Removes the node from the graph."""
        self.nodes.remove(n)

        # remove all vertices that point to it
        for node in self.nodes:
            if n in node.adjacent:
                del node.adjacent[n]

    @recalculate_components
    def add_vertex(self, n1: Node, n2: Node, weight: Union[int, float] = None):
        """Adds a vertex from node n1 to node n2 (and vice versa, if it's not directed).
        Only does so if the given vertex doesn't already exist and can be added (ex.:
        if the graph is not directed and the node wants to point to itself)."""
        if n1 is n2 and not self.directed:
            return

        # from n1 to n2
        n1.adjacent[n2] = weight

        # from n2 to n1
        if not self.directed:
            n2.adjacent[n1] = weight

    def is_vertex(self, n1: Node, n2: Node) -> bool:
        """Returns True if a vertex exists between the two nodes and False otherwise."""
        return n2 in n1.adjacent

    def toggle_vertex(self, n1: Node, n2: Node):
        """Toggles a connection between to vertexes."""
        if self.is_vertex(n1, n2):
            self.remove_vertex(n1, n2)
        else:
            self.add_vertex(n1, n2)

    @recalculate_components
    def remove_vertex(self, n1: Node, n2: Node):
        """Removes a vertex from node n1 to node n2 (and vice versa, if it's not 
        directed). Only does so if the given vertex exists."""
        # from n1 to n2
        if n2 in n1.adjacent:
            del n1.adjacent[n2]

        # from n2 to n1
        if not self.directed and n1 in n2.adjacent:
            del n2.adjacent[n1]

    @classmethod
    def from_string(cls, string: str, node_cls: Node = Node) -> type(cls):
        """Generates the graph from a given string."""
        graph = None
        node_dictionary = {}

        # add each of the nodes of the given line to the graph
        for line in filter(lambda x: len(x) != 0 or x[0] != "#", string.splitlines()):
            parts = line.strip().split()

            # initialize the graph from the first line, if it hasn't been done yet
            if graph is None:
                directed = parts[1] in ("->", "<-")
                weighted = len(parts) == 3 + directed

                graph = cls(directed=directed, weighted=weighted)

            # the formats are either 'A B' or 'A <something> B'
            node_names = (parts[0], parts[1 + directed])

            # if weight is present, the formats are:
            # - 'A B num' for undirected graphs
            # - 'A <something> B num' for directed graphs
            weight = 0 if not weighted else literal_eval(parts[2 + directed])

            # create node objects for each of the names (if it hasn't been done yet)
            for name in node_names:
                if name not in node_dictionary:
                    # add it to graph with default values
                    node_dictionary[name] = node_cls(label=name)
                    graph.add_node(node_dictionary[name])

            # get the node objects from the names
            n1, n2 = node_dictionary[node_names[0]], node_dictionary[node_names[1]]

            # possibly switch places for a reverse arrow
            if parts[1] == "<-":
                n1, n2 = n2, n1

            # add the vertex
            graph.add_vertex(n1, n2, weight)

        return graph

    def to_string(self) -> str:
        """Exports the graph, returning the string."""
        string = ""

        # TODO: make the counter check, if some nodes don't already have the same label
        counter = 0  # for naming nodes that don't have a label

        # for each pair n1, n2 where n1_i < n2_i
        for i, n1 in enumerate(self.nodes):
            for n2 in self.nodes[i + 1 :]:
                n1_label = n1.get_label() or str(counter := counter + 1)
                n2_label = n2.get_label() or str(counter := counter + 1)

                # TODO: simplify this code
                if self.is_vertex(n1, n2):
                    string += (
                        n1_label
                        + (" -> " if self.directed else " ")
                        + n2_label
                        + (str(self.get_weight(n1, n2)) if self.weighted else "")
                        + "\n"
                    )

                if self.is_vertex(n2, n1) and self.directed:
                    string += (
                        n1_label
                        + (" <- " if self.directed else " ")
                        + n2_label
                        + (str(self.get_weight(n2, n1)) if self.weighted else "")
                        + "\n"
                    )

        return string

    def to_asymptote(self) -> str:
        # TODO possible export option
        pass

    def to_tikz(self) -> str:
        # TODO possible export option
        pass

    def to_svg(self) -> str:
        # TODO possible export option
        pass


class Drawable(ABC):
    """Something that can be drawn on the PyQt5 canvas."""

    @abstractmethod
    def draw(self, painter: QPainter, palette: QPalette):
        """A method that draws the object on the canvas. Takes the painter to paint on
        and the palette to generate relative colors from."""


class DrawableNode(Drawable, Node):
    def __init__(self, position=Vector(0, 0), *args, **kwargs):
        self.position: Vector = position

        super().__init__(*args, **kwargs)

        self.forces: List[Vector] = []

        # for drawing the node itself
        self.pen = Pen(DEFAULT, Qt.SolidLine)
        self.brush = Brush(DEFAULT, Qt.SolidPattern)

        # for drawing the outgoing vertices
        self.adjacent_pens: Dict[Node, Pen] = {}

        # for information about being dragged
        # at that point, no forces act on it
        self.drag: Union[Vector, None] = None

        # whether it's currently selected or not
        self.selected = False

    def get_adjacent(self) -> Dict[Node, Union[int, float]]:
        """Returns nodes adjacent to the node."""
        return self.adjacent

    def get_position(self) -> Vector:
        """Return the position of the node."""
        return self.position

    def set_position(self, position: Vector):
        """Set the position of the node (accounted for drag)."""
        self.position = position - (self.drag or Vector(0, 0))

    def start_drag(self, position: Vector):
        """Start dragging the node, setting its drag offset from the mouse."""
        self.drag = position - self.get_position()

    def stop_drag(self) -> Vector:
        """Stop dragging the node."""
        self.drag = None

    def is_dragged(self) -> bool:
        """Return true if the node is currently in a dragged state."""
        return self.drag is not None

    def select(self):
        """Mark the node as selected."""
        self.brush.color = SELECTED
        self.selected = True

    def deselect(self):
        """Mark the node as not selected."""
        self.brush.color = DEFAULT
        self.selected = False

    def is_selected(self) -> bool:
        """Return, whether the node is selected or not."""
        return self.selected

    def add_force(self, force: Vector):
        """Adds a force that is acting upon the node to the force list."""
        self.forces.append(force)

    def evaluate_forces(self):
        """Evaluates all of the forces acting upon the node and moves it accordingly.
        Node that they are only applied if the note is not being dragged."""
        while len(self.forces) != 0:
            force = self.forces.pop()

            if not self.is_dragged():
                self.position += force

    def draw(self, painter: QPainter, palette: QPalette):
        """Draw the node at its current position with radius 1."""
        painter.setBrush(self.brush(palette))
        painter.setPen(self.pen(palette))

        painter.drawEllipse(QPointF(*self.position), 1, 1)


class DrawableGraph(Drawable, Graph):
    arrowhead_size: float = 0.5
    arrow_separation: float = pi / 7

    def draw(self, painter: QPainter, palette: QPalette):
        """Draw the entire graph."""
        # first, draw all vertices
        for node in self.get_nodes():
            for adjacent in node.get_adjacent():
                self.__draw_vertex(painter, palette, node, adjacent)

        # then, draw all nodes
        for node in self.get_nodes():
            node.draw(painter, palette)

    def get_selected(self) -> List[DrawableNode]:
        """Yield all currently selected nodes."""
        return [node for node in self.get_nodes() if node.is_selected()]

    def add_vertex(self, n1: Node, n2: Node, weight: Union[int, float] = None):
        """A wrapper around the normal Graph() add_vertex function that also adds the
        pen function with which to draw the vertex."""
        n1.adjacent_pens[n2] = Pen(DEFAULT, Qt.SolidLine)

        if not self.directed:
            n2.adjacent_pens[n1] = Pen(DEFAULT, Qt.SolidLine)

        super().add_vertex(n1, n2, weight)

    def __draw_vertex(
        self, painter: QPainter, palette: QPalette, n1: DrawableNode, n2: DrawableNode
    ):
        """Draw the specified vertex."""
        painter.setPen(n1.adjacent_pens[n2](palette))

        # special case for a node pointing to itself
        if n1 is n2:
            return  # TODO special case for a loop
        else:
            start, end = self.__get_vertex_position(n1, n2)

            # draw the head of a directed arrow, which is an equilateral triangle
            if self.get_directed():
                uv = (end - start).unit()

                # the brush color is given by the current pen
                painter.setBrush(QBrush(painter.pen().color(), Qt.SolidPattern))
                painter.drawPolygon(
                    QPointF(*end),
                    QPointF(*(end + (-uv).rotated(radians(30)) * self.arrowhead_size)),
                    QPointF(*(end + (-uv).rotated(radians(-30)) * self.arrowhead_size)),
                )

        painter.drawLine(QPointF(*start), QPointF(*end))

        if self.get_weighted():
            pass  # TODO draw the weight

    def __get_vertex_position(self, n1: Node, n2: Node) -> Tuple[Vector, Vector]:
        """Return the position of the vertex on the screen."""
        # positions of the nodes
        n1_p = Vector(*n1.get_position())
        n2_p = Vector(*n2.get_position())

        # unit vector from n1 to n2
        uv = (n2_p - n1_p).unit()

        # start and end of the vertex to be drawn
        start = n1_p + uv
        end = n2_p - uv

        if self.get_directed():
            # if the graph is directed and a vertex exists that goes the other way, we
            # have to move the start end end so the vertexes don't overlap
            if self.is_vertex(n2, n1):
                start = start.rotated(self.arrow_separation, n1_p)
                end = end.rotated(-self.arrow_separation, n2_p)

        return start, end

    def node_at_position(self, position: Vector) -> Union[None, DrawableNode]:
        """Returns a Node if it is at the given position, or None."""
        for node in self.get_nodes():
            if position.distance(node.get_position()) <= 1:
                return node
