"""A wrapper for working with graphs that can be drawn."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import *

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ast import literal_eval
from collections import defaultdict
from math import sqrt, cos, sin, radians, pi
from abc import *

from grafatko.utilities import *
from grafatko.colors import *


@dataclass(eq=False)
class Node:
    """A class for working with of nodes in a graph."""

    label: str = None
    adjacent: Dict[Node, Union[int, float]] = field(default_factory=dict)

    def get_adjacent(self) -> Dict[Node, Union[int, float]]:
        """Returns nodes adjacent to the node."""
        return self.adjacent

    def get_label(self) -> Optional[str]:
        """Returns the label of the node (or None if has none)."""
        return self.label

    def set_label(self, label: Optional[str]):
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

    def get_weakly_connected(self, *args: Sequence[Node]) -> List[Node]:
        """Return a list of all nodes that are weakly connected to any node from the
        given sequence."""
        nodes = set()

        for node in args:
            for component in self.components:
                if node in component:
                    nodes |= component

        return list(nodes)

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
        if not directed:
            for node in self.nodes:
                for neighbour in list(node.adjacent):
                    if node is neighbour:
                        # no loops allowed >:C
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

    def get_weight(self, n1: Node, n2: Node) -> Optional[Union[int, float]]:
        """Returns the weight of the specified vertex (and None if they're not connected)."""
        if self.is_vertex(n1, n2):
            return self.nodes[self.nodes.index(n1)].adjacent[n2]

    def get_nodes(self) -> List[Node]:
        """Returns a list of nodes of the graph."""
        return self.nodes

    @recalculate_components
    def add_node(self, node: Node):
        """Adds a new node to the graph."""
        self.nodes.append(node)

    def reorient(self):
        """Change the orientation of all vertices."""
        # for each pair of nodes
        for i, n1 in enumerate(self.get_nodes()):
            for n2 in self.get_nodes()[i:]:
                # change the direction, if there is only one
                if bool(self.is_vertex(n1, n2)) != bool(self.is_vertex(n2, n1)):  # xor
                    self.toggle_vertex(n1, n2)
                    self.toggle_vertex(n2, n1)

    def complement(self):
        """Complement the graph."""
        # for each pair of nodes
        for i, n1 in enumerate(self.get_nodes()):
            for n2 in self.get_nodes()[i:]:
                self.toggle_vertex(n1, n2)

                # also toggle the other way, if it's directed
                # node that I didn't deliberately put 'and n1 is not n2' here, since
                # they're special and we usually don't want them
                if self.get_directed():
                    self.toggle_vertex(n2, n1)

    @recalculate_components
    def remove_node(self, n: Node):
        """Removes the node from the graph."""
        self.nodes.remove(n)

        # remove all vertices that point to it
        for node in self.nodes:
            if n in node.adjacent:
                del node.adjacent[n]

    @recalculate_components
    def add_vertex(self, n1: Node, n2: Node, weight: Optional[Union[int, float]] = 1):
        """Adds a vertex from node n1 to node n2 (and vice versa, if it's not directed).
        Only does so if the given vertex doesn't already exist and can be added (ex.:
        if the graph is not directed and the node wants to point to itself)."""
        # special case for a loop
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
        """Toggles a connection between two nodes."""
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


class Drawable(ABC):
    """Something that can be drawn on the PyQt5 canvas."""

    @abstractmethod
    def draw(self, painter: QPainter, palette: QPalette, *args, **kwargs):
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
        # it's the offset from the mouse when the drag started
        self.drag: Optional[Vector] = None

        # whether it's currently selected or not
        self.selected = False

    def get_adjacent(self) -> Dict[Node, Union[int, float]]:
        """Returns nodes adjacent to the node."""
        return self.adjacent

    def get_position(self) -> Vector:
        """Return the position of the node."""
        return self.position

    def set_position(self, position: Vector, override_drag: bool = False):
        """Set the position of the node (accounted for drag). The override_drag option
        moves the node to the position even if it's currently being dragged."""
        if override_drag and self.is_dragged():
            self.drag += self.position - position
        else:
            self.position = position - (self.drag or Vector(0, 0))

    def start_drag(self, mouse_position: Vector):
        """Start dragging the node, setting its drag offset from the mouse."""
        self.drag = mouse_position - self.get_position()

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

    def clear_forces(self):
        """Clear all of the forces from the node."""
        self.forces = []

    def draw(self, painter: QPainter, palette: QPalette, draw_label=False):
        """Draw the node at its current position with radius 1."""
        painter.setBrush(self.brush(palette))
        painter.setPen(self.pen(palette))

        painter.drawEllipse(QPointF(*self.position), 1, 1)

        # possibly draw the label of the node
        if draw_label and self.get_label() is not None:
            label = self.get_label()
            mid = self.get_position()

            # get the rectangle that surrounds the label
            r = QFontMetrics(painter.font()).boundingRect(label)
            scale = 1.9 / Vector(r.width(), r.height()).magnitude()

            # draw it on the screen
            size = Vector(r.width(), r.height()) * scale
            rect = QRectF(*(mid - size / 2), *size)

            painter.save()

            painter.setBrush(Brush(BACKGROUND)(palette))
            painter.setPen(Pen(BACKGROUND)(palette))

            # translate to top left and scale down to draw the actual text
            painter.translate(rect.topLeft())
            painter.scale(scale, scale)

            painter.drawText(
                QRectF(0, 0, rect.width() / scale, rect.height() / scale),
                Qt.AlignCenter,
                label,
            )

            painter.restore()


class DrawableGraph(Drawable, Graph):
    font: QFont = None  # the font that is used to draw the weights

    # possible TODO: compute this programatically
    text_scale: Final[float] = 0.04  # the constant by which to scale down the font

    arrowhead_size: Final[float] = 0.5  # how big is the head triangle
    arrow_separation: Final[float] = pi / 7  # how far apart are two-way vertices
    loop_arrowhead_angle: Final[float] = -30.0  # an angle for the head in a loop

    show_labels: bool = False  # whether or not to show the labels of nodes

    # a dictionary for calculating the distance from a root node
    # used in displaying the graph as a tree
    distance_from_root = {}
    root = None

    def draw(self, painter: QPainter, palette: QPalette):
        """Draw the entire graph."""
        self.font = painter.font()

        # first, draw all vertices
        for node in self.get_nodes():
            for adjacent in node.get_adjacent():
                # don't draw both ways if the graph is not oriented
                if self.get_directed() or id(node) < id(adjacent):
                    self.__draw_vertex(painter, palette, node, adjacent)

        # then, draw all nodes
        for node in self.get_nodes():
            node.draw(painter, palette, self.show_labels)

    def get_selected(self) -> List[DrawableNode]:
        """Yield all currently selected nodes."""
        return [node for node in self.get_nodes() if node.is_selected()]

    def set_show_labels(self, value: bool):
        """Whether to show the node labels or not."""
        self.show_labels = value

    def recalculate_distance_to_root(function):
        """A decorator for recalculating the distance from the root node to the rest of
        the graph."""

        def wrapper(self, *args, **kwargs):
            # first add/remove vertex/node/whatever
            function(self, *args, **kwargs)

            self.distance_from_root = {}

            # don't do anything if the root
            if self.get_root() is None:
                return

            # else run the BFS to calculate the distances
            queue = [(self.root, 1)]
            closed = set()
            self.distance_from_root[0] = [self.root]

            while len(queue) != 0:
                current, distance = queue.pop(0)

                for adjacent in current.get_adjacent():
                    if adjacent not in closed:
                        if distance not in self.distance_from_root:
                            self.distance_from_root[distance] = []

                        queue.append((adjacent, distance + 1))
                        self.distance_from_root[distance].append(adjacent)

                closed.add(current)

        return wrapper

    @recalculate_distance_to_root
    def set_root(self, node: DrawableNode):
        """Set a node as the root of the tree."""
        self.root = node

    def get_root(self) -> Optional[DrawableNode]:
        """Return the root of the tree (or None if there is none)."""
        return self.root

    @recalculate_distance_to_root
    def add_vertex(self, n1: Node, n2: Node, *args, **kwargs):
        """A wrapper around the normal Graph() add_vertex function that also adds the
        pen function with which to draw the vertex."""
        n1.adjacent_pens[n2] = Pen(DEFAULT, Qt.SolidLine)

        if not self.directed:
            n2.adjacent_pens[n1] = Pen(DEFAULT, Qt.SolidLine)

        super().add_vertex(n1, n2, *args, **kwargs)

    @recalculate_distance_to_root
    def remove_vertex(self, *args, **kwargs):
        super().remove_vertex(*args, **kwargs)

    @recalculate_distance_to_root
    def add_node(self, *args, **kwargs):
        super().add_node(*args, **kwargs)

    @recalculate_distance_to_root
    def remove_node(self, node, **kwargs):
        # check, if we're not removing the root; if we are, act accordingly
        if node is self.root:
            self.set_root(None)

        super().remove_node(node, **kwargs)

    def __draw_vertex(
        self, painter: QPainter, palette: QPalette, n1: DrawableNode, n2: DrawableNode
    ):
        """Draw the specified vertex."""
        painter.setPen(n1.adjacent_pens[n2](palette))
        painter.setBrush(Qt.NoBrush)

        # special case for a loop
        if n1 is n2:
            # draw the ellipse that symbolizes a loop
            center = n1.get_position() - Vector(0.5, 1)
            painter.drawEllipse(QPointF(*center), 0.5, 0.5)

            # draw the head of the loop arrow
            head_direction = Vector(0, 1).rotated(radians(self.loop_arrowhead_angle))
            self.__draw_arrow_tip(center + Vector(0.5, 0), head_direction, painter)
        else:
            start, end = self.__get_vertex_position(n1, n2)

            # draw the line
            painter.drawLine(QPointF(*start), QPointF(*end))

            # draw the head of a directed arrow, which is an equilateral triangle
            if self.get_directed():
                self.__draw_arrow_tip(end, end - start, painter)

        # draw the weight
        if self.get_weighted():
            # set the color to be the same as the vertex
            color = n1.adjacent_pens[n2].color(palette)
            painter.setBrush(QBrush(color, Qt.SolidPattern))

            painter.save()

            # draw the bounding box
            rect = self.__get_weight_box(n1, n2)
            painter.drawRect(rect)

            painter.setBrush(Brush(BACKGROUND)(palette))
            painter.setPen(Pen(BACKGROUND)(palette))

            scale = self.text_scale

            # translate to top left and scale down to draw the actual text
            painter.translate(rect.topLeft())
            painter.scale(scale, scale)

            painter.drawText(
                QRectF(0, 0, rect.width() / scale, rect.height() / scale),
                Qt.AlignCenter,
                str(n1.get_adjacent()[n2]),
            )

            painter.restore()

    def __get_weight_box(self, n1: DrawableNode, n2: DrawableNode) -> QRectF:
        """Get the rectangle that the weight of n1->n2 vertex will be drawn in."""
        # get the rectangle that bounds the text (according to the current font metric)
        metrics = QFontMetrics(self.font)
        r = metrics.boundingRect(str(n1.get_adjacent()[n2]))

        # get the mid point of the weight box, depending on whether it's a loop or not
        if n1 is n2:
            # the distance from the center of the node to the side of the ellipse that
            # is drawn to symbolize the loop
            offset = Vector(0.5, 1) + Vector(0.5, 0).rotated(radians(45))
            mid = n1.get_position() - offset
        else:
            mid = Vector.average(self.__get_vertex_position(n1, n2))

        # scale it down by text_scale before returning it
        # if width is smaller then height, set it to height
        height = r.height()
        width = r.width() if r.width() >= height else height

        size = Vector(width, height) * self.text_scale
        return QRectF(*(mid - size / 2), *size)

    def __draw_arrow_tip(self, pos: Vector, direction: Vector, painter: QPainter):
        """Draw the tip of the vertex (as a triangle)."""
        uv = direction.unit()

        # the brush color is given by the current pen
        painter.setBrush(QBrush(painter.pen().color(), Qt.SolidPattern))
        painter.drawPolygon(
            QPointF(*pos),
            QPointF(*(pos + (-uv).rotated(radians(30)) * self.arrowhead_size)),
            QPointF(*(pos + (-uv).rotated(radians(-30)) * self.arrowhead_size)),
        )

    def __get_vertex_position(self, n1: Node, n2: Node) -> Tuple[Vector, Vector]:
        """Return the starting and ending position of the vertex on the screen."""
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

    def select_all(self):
        """Select all nodes."""
        for node in self.get_nodes():
            node.select()

    def deselect_all(self):
        """Deselect all nodes."""
        for node in self.get_nodes():
            node.deselect()

    def node_at_position(self, position: Vector) -> Optional[DrawableNode]:
        """Returns a Node if there is one at the given position, else None."""
        for node in self.get_nodes():
            if position.distance(node.get_position()) <= 1:
                return node

    def get_distance_from_root(self) -> Dict[int, List[DrawableNode]]:
        """Return the resulting dictionary of a BFS ran from the root node."""
        return self.distance_from_root

    def vertex_at_position(
        self, position: Vector
    ) -> Optional[Tuple[DrawableNode, DrawableNode]]:
        """Returns a vertex if there is one at the given position, else None."""
        for n1 in self.get_nodes():
            for n2 in n1.get_adjacent():
                if self.__get_weight_box(n1, n2).contains(*position):
                    return (n1, n2)

    def to_asymptote(self) -> str:
        # TODO possible export option
        pass

    def to_tikz(self) -> str:
        # TODO possible export option
        pass

    def to_svg(self) -> str:
        # TODO possible export option
        pass
