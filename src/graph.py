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

from abc import *


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

    def add_node(self, node: Node):
        """Adds a new node to the graph."""
        self.nodes.append(node)

    def remove_node(self, n: Node):
        """Removes the node from the graph."""
        self.nodes.remove(n)

        # remove all vertices that point to it
        for node in self.nodes:
            if n in node.adjacent:
                del node.adjacent[n]

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
    def from_string(cls, string: str) -> Graph:
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

                graph = Graph(directed=directed, weighted=weighted)

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
                    node_dictionary[name] = Node(label=name)
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

        # for each pair n1, n2 where n1_i < n2_i
        for i, n1 in enumerate(self.nodes):
            for n2 in self.nodes[i + 1 :]:
                # TODO: simplify this code
                if self.is_vertex(n1, n2):
                    string += (
                        n1.get_label()
                        + (" -> " if self.directed else " ")
                        + n2.get_label()
                        + (str(self.get_weight(n1, n2)) if self.weighted else "")
                        + "\n"
                    )

                if self.is_vertex(n2, n1) and self.directed:
                    string += (
                        n1.get_label()
                        + (" <- " if self.directed else " ")
                        + n2.get_label()
                        + (str(self.get_weight(n2, n1)) if self.weighted else "")
                        + "\n"
                    )

        return string


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
        # TODO take this from a configuration file
        self.pen: QPen = QPen(Qt.red, Qt.SolidLine)
        self.brush: QBrush = QBrush(Qt.red, Qt.SolidPattern)

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

    def draw(self, painter: QPainter):
        """Draw the node at its current position with radius 1."""
        painter.setBrush(self.brush)
        painter.setPen(self.pen)

        painter.drawEllipse(QPointF(*self.position), 1, 1)


class DrawableGraph(Drawable, Graph):
    def draw(self, painter: QPainter):
        """Draw the entire graph."""
        # TODO draw all vertices

        # draw all nodes
        for node in self.get_nodes():
            node.draw(painter)

    def node_at_position(self, position: Vector) -> Union[None, DrawableNode]:
        """Returns a Node if it is at the given position, or None."""
        for node in self.get_nodes():
            if position.distance(node.get_position()) <= 1:
                return node
