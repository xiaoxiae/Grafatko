# math
from math import sqrt, cos, sin, radians, pi
from random import random

import sys  # for argv
import ast  # parsing

from typing import Tuple

# PyQt5
from PyQt5.QtCore import Qt, QSize, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QSizePolicy,
)

# graph stuff
from graph import Graph, Node

# utilities stuff
from utilities import *


class TreeVisualizer(QWidget):
    def __init__(self):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        # graph variables
        self.graph: Graph = Graph()
        self.selected_node: Node = None

        self.selected_vertex: Tuple[Node, Node] = None

        # offset of the mouse from the position of the currently dragged node
        self.mouse_drag_offset: Vector = None

        # position of the mouse; is updated when the mouse moves
        self.mouse_position: Vector = Vector(-1, -1)

        # variables for visualizing the graph
        self.node_radius: float = 20
        self.weight_rectangle_size: float = self.node_radius / 3

        self.arrowhead_size: float = 8
        self.arrow_separation: float = pi / 7

        self.selected_color = Qt.red
        self.regular_node_color = Qt.white
        self.regular_vertex_weight_color = Qt.black

        # limit the displayed length of labels for each node
        self.node_label_limit: int = 10

        # UI variables
        self.font_family: str = "Times New Roman"
        self.font_size: int = 18

        self.layout_margins: float = 8
        self.layout_item_spacing: float = 2 * self.layout_margins

        # canvas positioning (scale and translation)
        self.scale: float = 1
        self.scale_coefficient: float = 2  # by how much the scale changes on scroll
        self.translation: float = Vector(0, 0)

        # by how much the rotation of the nodes changes
        self.node_rotation_coefficient: float = 0.7

        # TIMERS
        # timer that runs the simulation (60 times a second... once every ~= 16ms)
        self.simulation_timer = QTimer(
            interval=16, timeout=self.perform_simulation_iteration
        )

        # WIDGETS
        self.canvas = QFrame(self, minimumSize=QSize(0, 400))
        self.canvas_size: Vector = None
        self.canvas.resizeEvent = self.adjust_canvas_translation

        # toggles between directed/undirected graphs
        self.directed_toggle_button = QPushButton(
            text="undirected", clicked=self.toggle_directed_graph
        )

        # for showing the labels of the nodes
        self.labels_checkbox = QCheckBox(text="labels")

        # sets, whether the graph is weighted or not
        self.weighted_checkbox = QCheckBox(
            text="weighted", clicked=self.set_weighted_graph
        )

        # enables/disables forces (True by default - they're fun!)
        self.forces_checkbox = QCheckBox(text="forces", checked=True)

        # input of the labels and vertex weights
        self.input_line_edit = QLineEdit(
            enabled=self.labels_checkbox.isChecked(),
            textChanged=self.input_line_edit_changed,
        )

        # displays information about the app
        self.about_button = QPushButton(
            text="?",
            clicked=self.show_help,
            sizePolicy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed),
        )

        # for creating complements of the graph
        self.complement_button = QPushButton(
            text="complement", clicked=self.graph.complement,
        )

        # imports/exports the current graph
        self.import_graph_button = QPushButton(text="import", clicked=self.import_graph)
        self.export_graph_button = QPushButton(text="export", clicked=self.export_graph)

        # WIDGET LAYOUT
        self.main_v_layout = QVBoxLayout(self, margin=0)
        self.main_v_layout.addWidget(self.canvas)

        self.option_h_layout = QHBoxLayout(self, margin=self.layout_margins)
        self.option_h_layout.addWidget(self.directed_toggle_button)
        self.option_h_layout.addSpacing(self.layout_item_spacing)
        self.option_h_layout.addWidget(self.weighted_checkbox)
        self.option_h_layout.addSpacing(self.layout_item_spacing)
        self.option_h_layout.addWidget(self.labels_checkbox)
        self.option_h_layout.addSpacing(self.layout_item_spacing)
        self.option_h_layout.addWidget(self.forces_checkbox)
        self.option_h_layout.addSpacing(self.layout_item_spacing)
        self.option_h_layout.addWidget(self.input_line_edit)

        self.bottom_h_layout = QHBoxLayout(self, margin=self.layout_margins)
        self.bottom_h_layout.addWidget(self.complement_button)
        self.bottom_h_layout.addSpacing(self.layout_item_spacing)
        self.bottom_h_layout.addWidget(self.import_graph_button)
        self.bottom_h_layout.addSpacing(self.layout_item_spacing)
        self.bottom_h_layout.addWidget(self.export_graph_button)
        self.bottom_h_layout.addSpacing(self.layout_item_spacing)
        self.bottom_h_layout.addWidget(self.about_button)

        self.main_v_layout.addLayout(self.option_h_layout)
        self.main_v_layout.addSpacing(-self.layout_margins)
        self.main_v_layout.addLayout(self.bottom_h_layout)

        self.setLayout(self.main_v_layout)

        # WINDOW SETTINGS
        self.setWindowTitle("Graph Visualizer")
        self.setFont(QFont(self.font_family, self.font_size))
        self.setWindowIcon(QIcon("icon.ico"))
        self.show()

        # start the simulation
        self.simulation_timer.start()

    def set_weighted_graph(self):
        """Is called when the weighted checkbox is pressed; sets, whether the graph is 
        weighted or not."""
        self.graph.set_weighted(self.weighted_checkbox.isChecked())

    def adjust_canvas_translation(self, event):
        """Is called when the canvas widget is resized; changes translation so the 
        center stays in the center."""
        size = Vector(event.size().width(), event.size().height())

        if self.canvas_size is not None:
            self.translation += self.scale * (size - self.canvas_size) / 2

        self.canvas_size = size

    def repulsion_force(self, distance: float) -> float:
        """Calculates the strength of the repulsion force at the specified distance."""
        return 1 / distance * 10 if self.forces_checkbox.isChecked() else 0

    def attraction_force(self, distance: float, leash_length=80) -> float:
        """Calculates the strength of the attraction force at the specified distance 
        and leash length."""
        return (
            -(distance - leash_length) / 10 if self.forces_checkbox.isChecked() else 0
        )

    def import_graph(self):
        """Is called when the import button is clicked; imports a graph from a file."""
        path = QFileDialog.getOpenFileName()[0]

        if path != "":
            try:
                with open(path, "r") as file:
                    # a list of vertices of the graph
                    data = [line.strip() for line in file.read().splitlines()]

                    # set the properties of the graph by its first vertex
                    sample = data[0].split(" ")

                    directed = True if sample[1] in ["->", "<-", "<>"] else False
                    weighted = (
                        False
                        if len(sample) == 2 or directed and len(sample) == 3
                        else True
                    )

                    graph = Graph(directed=directed, weighted=weighted)

                    node_dictionary = {}

                    # add each of the nodes of the vertex to the graph
                    for vertex in data:
                        vertex_components = vertex.split(" ")

                        # the formats are either 'A B' or 'A <something> B'
                        nodes = [
                            vertex_components[0],
                            vertex_components[2] if directed else vertex_components[1],
                        ]

                        # if weights are present, the formats are:
                        # - 'A B num' for undirected graphs
                        # - 'A <something> B num (num)' for directed graphs
                        weights_strings = (
                            None
                            if not weighted
                            else [
                                vertex_components[2]
                                if not directed
                                else vertex_components[3],
                                None
                                if not directed or vertex_components[1] != "<>"
                                else vertex_components[4],
                            ]
                        )

                        for node in nodes:
                            if node not in node_dictionary:
                                # slightly randomize the coordinates, so the graph
                                # doesn't stay in one place
                                x = self.canvas.width() / 2 + (random() - 0.5)
                                y = self.canvas.height() / 2 + (random() - 0.5)

                                # add it to graph with default values
                                node_dictionary[node] = graph.add_node(
                                    Vector(x, y), self.node_radius, node
                                )

                        # get the node objects from the names
                        n1, n2 = node_dictionary[nodes[0]], node_dictionary[nodes[1]]

                        graph.add_vertex(
                            n2 if vertex_components[1] == "<-" else n1,
                            n1 if vertex_components[1] == "<-" else n2,
                            0 if not weighted else ast.literal_eval(weights_strings[0]),
                        )

                        # possibly add the other way
                        if vertex_components[1] == "<>":
                            graph.add_vertex(
                                n2,
                                n1,
                                0
                                if not weighted
                                else ast.literal_eval(weights_strings[1]),
                            )

                # if everything was successful, override the current graph
                self.graph = graph

            except UnicodeDecodeError:
                QMessageBox.critical(self, "Error!", "Can't read binary files!")
            except ValueError:
                QMessageBox.critical(
                    self, "Error!", "The weights of the graph are not numbers!"
                )
            except Exception:
                QMessageBox.critical(
                    self,
                    "Error!",
                    "An error occurred when importing the graph. Make sure that the "
                    + "file is in the correct format and that it isn't currently being "
                    + "used!",
                )

            # make sure that the UI is in order
            self.deselect_node()
            self.deselect_vertex()
            self.set_checkbox_values()

    def set_checkbox_values(self):
        """Sets the values of the checkboxes from the graph."""
        self.weighted_checkbox.setChecked(self.graph.is_weighted())
        self.update_directed_toggle_button_text()

    def export_graph(self):
        """Is called when the export button is clicked; exports a graph to a file."""
        path = QFileDialog.getSaveFileName()[0]

        if path != "":
            try:
                with open(path, "w") as file:
                    # look at every pair of nodes and examine the vertices
                    for i, n1 in enumerate(self.graph.get_nodes()):
                        for j, n2 in enumerate(self.graph.get_nodes()[i + 1 :]):
                            # information about vertices and weights
                            v1_exists = self.graph.does_vertex_exist(n1, n2)
                            v2_exists = self.graph.does_vertex_exist(n2, n1)

                            if not v1_exists and v2_exists:
                                continue

                            w1_value = self.graph.get_weight(n1, n2)
                            w1 = (
                                ""
                                if not self.graph.is_weighted() or w1_value is None
                                else str(w1_value)
                            )

                            # undirected graphs
                            if not self.graph.is_directed() and v1_exists:
                                file.write(f"{n1.get_label()} {n2.get_label()} {w1}\n")
                            else:
                                w2_value = self.graph.get_weight(n2, n1)
                                w2 = (
                                    ""
                                    if not self.graph.is_weighted() or w2_value is None
                                    else str(w2_value)
                                )

                                symbol = (
                                    "<>"
                                    if v1_exists and v2_exists
                                    else "->"
                                    if v1_exists
                                    else "<-"
                                )

                                vertex = f"{n1.get_label()} {symbol} {n2.get_label()}"

                                if w1 != "":
                                    vertex += f" {w1}"
                                if w2 != "":
                                    vertex += f" {w2}"

                                file.write(vertex + "\n")
            except Exception:
                QMessageBox.critical(
                    self,
                    "Error!",
                    "An error occurred when exporting the graph. Make sure that you "
                    "have permission to write to the specified file and try again!",
                )

    def show_help(self):
        """Is called when the help button is clicked; displays basic information about 
        the application."""
        message = """
            <p>Welcome to <strong>Graph Visualizer</strong>.</p>
            <p>The app aims to help with creating, visualizing and exporting graphs. 
            It is powered by PyQt5 &ndash; a set of Python bindings for the C++ library Qt.</p>
            <hr />
            <p>The controls are as follows:</p>
            <ul>
            <li><em>Left Mouse Button</em> &ndash; selects nodes and moves them</li>
            <li><em>Right Mouse Button</em> &ndash; creates/removes nodes and vertices</li>
            <li><em>Mouse Wheel</em> &ndash; zooms in/out</li>
            <li><em>Shift + Left Mouse Button</em> &ndash; moves connected nodes</li>
            <li><em>Shift + Mouse Wheel</em> &ndash; rotates nodes around the selected node</li>
            </ul>
            <hr />
            <p>If you spot an issue, or would like to check out the source code, see the app's 
            <a href="https://github.com/xiaoxiae/GraphVisualizer">GitHub repository</a>.</p>
        """

        QMessageBox.information(self, "About", message)

    def toggle_directed_graph(self):
        """Is called when the directed checkbox changes; toggles between directed and 
        undirected graphs."""
        self.graph.set_directed(not self.graph.is_directed())
        self.update_directed_toggle_button_text()

    def update_directed_toggle_button_text(self):
        """Changes the text of the directed toggle button, according to whether the 
        graph is directer or not."""
        self.directed_toggle_button.setText(
            "directed" if self.graph.is_directed() else "undirected"
        )

    def input_line_edit_changed(self, text: str):
        """Is called when the input line edit changes; changes either the label of the 
        node selected node, or the value of the selected vertex."""
        palette = self.input_line_edit.palette()
        text = text.strip()

        if self.selected_node is not None:
            # text is restricted for rendering and graph export purposes
            if 0 < len(text) < self.node_label_limit and " " not in text:
                self.selected_node.set_label(text)
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.white)
            else:
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.red)
        elif self.selected_vertex is not None:
            # try to parse the input text either as an integer, or as a float
            weight = None
            try:
                weight = int(text)
            except ValueError:
                try:
                    weight = float(text)
                except ValueError:
                    pass

            # if the parsing was unsuccessful, set the input line edit background to
            # red to indicate this
            if weight is None:
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.red)
            else:
                self.graph.add_vertex(
                    self.selected_vertex[0], self.selected_vertex[1], weight
                )
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.white)

        self.input_line_edit.setPalette(palette)

    def select_node(self, node: Node):
        """Sets the selected node to the specified node, sets the input line edit to 
        its label and enables it."""
        self.selected_node = node

        self.input_line_edit.setText(node.get_label())
        self.input_line_edit.setEnabled(True)
        self.input_line_edit.setFocus()

    def deselect_node(self):
        """Sets the selected node to None and disables the input line edit."""
        self.selected_node = None
        self.input_line_edit.setEnabled(False)

    def select_vertex(self, vertex):
        """Sets the selected vertex to the specified vertex, sets the input line edit to
        its weight and enables it."""
        self.selected_vertex = vertex

        self.input_line_edit.setText(str(self.graph.get_weight(*vertex)))
        self.input_line_edit.setEnabled(True)
        self.input_line_edit.setFocus()

    def deselect_vertex(self):
        """Sets the selected vertex to None and disables the input line edit."""
        self.selected_vertex = None
        self.input_line_edit.setEnabled(False)

    def mousePressEvent(self, event):
        """Is called when a mouse button is pressed; creates and moves 
        nodes/vertices."""
        pos = self.get_mouse_position(event)

        # if we are not on canvas, don't do anything
        if pos is None:
            return

        # sets the focus to the window (for the keypresses to register)
        self.setFocus()

        # (potentially) find a node that has been pressed
        pressed_node = None
        for node in self.graph.get_nodes():
            if distance(pos, node.get_position()) <= node.get_radius():
                pressed_node = node

        # (potentially) find a vertex that has been pressed
        pressed_vertex = None
        if self.graph.is_weighted():
            for n1 in self.graph.get_nodes():
                for n2, weight in n1.get_neighbours().items():

                    if self.graph.is_directed() or id(n1) < id(n2):
                        weight = self.graph.get_weight(n1, n2)

                        # the bounding box of this weight
                        weight_rect = self.get_vertex_weight_rect(n1, n2, weight)
                        if weight_rect.contains(QPointF(*pos)):
                            pressed_vertex = (n1, n2)

        if event.button() == Qt.LeftButton:
            # nodes have the priority in selection over vertices
            if pressed_node is not None:
                self.deselect_vertex()
                self.select_node(pressed_node)

                self.mouse_drag_offset = pos - self.selected_node.get_position()
                self.mouse_position = pos

            elif pressed_vertex is not None:
                self.deselect_node()
                self.select_vertex(pressed_vertex)

            else:
                self.deselect_node()
                self.deselect_vertex()

        elif event.button() == Qt.RightButton:
            if pressed_node is not None:
                if self.selected_node is not None:
                    self.graph.toggle_vertex(self.selected_node, pressed_node)
                else:
                    self.graph.remove_node(pressed_node)
                    self.deselect_node()

            elif pressed_vertex is not None:
                self.graph.remove_vertex(*pressed_vertex)
                self.deselect_vertex()

            else:
                node = self.graph.add_node(pos, self.node_radius)

                # if a selected node exists, connect it to the newly created node
                if self.selected_node is not None:
                    self.graph.add_vertex(self.selected_node, node)

                self.select_node(node)
                self.deselect_vertex()

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released; stops node drag."""
        self.mouse_drag_offset = None

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window; updates mouse 
        coordinates."""
        self.mouse_position = self.get_mouse_position(event, scale_down=True)

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; node rotation and zoom."""
        # positive/negative for scrolling away from/towards the user
        scroll_distance = radians(event.angleDelta().y() / 8)

        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            if self.selected_node is not None:
                self.rotate_nodes_around(
                    self.selected_node.get_position(),
                    scroll_distance * self.node_rotation_coefficient,
                )
        else:
            mouse_coordinates = self.get_mouse_position(event)

            # only do something, if we're working on canvas
            if mouse_coordinates is None:
                return

            prev_scale = self.scale
            self.scale *= 2 ** (scroll_distance)

            # adjust translation so the x and y of the mouse stay in the same spot
            self.translation -= mouse_coordinates * (self.scale - prev_scale)

    def rotate_nodes_around(self, point: Vector, angle: float):
        """Rotates coordinates of all of the nodes in the same component as the selected 
        node by a certain angle (in radians) around it."""
        for node in self.graph.get_nodes():
            if self.graph.share_component(node, self.selected_node):
                node.set_position((node.position - point).rotated(angle) + point)

    def get_mouse_position(self, event, scale_down=False) -> Vector:
        """Returns mouse coordinates if they are within the canvas and None if they are 
        not. If scale_down is True, the function will scale down the coordinates to be 
        within the canvas (useful for dragging) and return them instead."""
        x = event.pos().x()
        y = event.pos().y()

        x_on_canvas = 0 <= x <= self.canvas.width()
        y_on_canvas = 0 <= y <= self.canvas.height()

        # scale down the coordinates if scale_down is True, or return None if we are
        # not on canvas
        if scale_down:
            x = x if x_on_canvas else 0 if x <= 0 else self.canvas.width()
            y = y if y_on_canvas else 0 if y <= 0 else self.canvas.height()
        elif not x_on_canvas or not y_on_canvas:
            return None

        # return the mouse coordinates, accounting for canvas translation and scale
        return (Vector(x, y) - self.translation) / self.scale

    def perform_simulation_iteration(self):
        """Performs one iteration of the simulation."""
        # evaluate forces that act upon each pair of nodes
        for i, n1 in enumerate(self.graph.get_nodes()):
            for j, n2 in enumerate(self.graph.get_nodes()[i + 1 :]):
                # if they are not in the same component, no forces act on them
                if not self.graph.share_component(n1, n2):
                    continue

                # if the nodes are right on top of each other, no forces act on them
                d = distance(n1.get_position(), n2.get_position())
                if n1.get_position() == n2.get_position():
                    continue

                uv = (n2.get_position() - n1.get_position()).unit()

                # the size of the repel force between the two nodes
                fr = self.repulsion_force(d)

                # add a repel force to each of the nodes, in the opposite directions
                n1.add_force(-uv * fr)
                n2.add_force(uv * fr)

                # if they are also connected, add the attraction force
                if self.graph.does_vertex_exist(n1, n2, ignore_direction=True):
                    fa = self.attraction_force(d)

                    n1.add_force(-uv * fa)
                    n2.add_force(uv * fa)

            # since this node will not be visited again, we can evaluate the forces
            n1.evaluate_forces()

        # drag the selected node
        if self.selected_node is not None and self.mouse_drag_offset is not None:
            prev_node_position = self.selected_node.get_position()

            self.selected_node.set_position(
                self.mouse_position - self.mouse_drag_offset
            )

            # move the rest of the nodes that are connected to the selected node if
            # shift is pressed
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                pos_delta = self.selected_node.get_position() - prev_node_position

                for node in self.graph.get_nodes():
                    if node is not self.selected_node and self.graph.share_component(
                        node, self.selected_node
                    ):
                        node.set_position(node.get_position() + pos_delta)

        self.update()

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        painter.setClipRect(0, 0, self.canvas.width(), self.canvas.height())

        # background
        painter.drawRect(0, 0, self.canvas.width(), self.canvas.height())

        painter.translate(*self.translation)
        painter.scale(self.scale, self.scale)

        # draw vertexes
        for n1 in self.graph.get_nodes():
            for n2, weight in n1.get_neighbours().items():
                self.draw_vertex(n1, n2, weight, painter)

        # draw nodes
        for node in self.graph.get_nodes():
            self.draw_node(node, painter)

    def draw_node(self, node: Node, painter):
        """Draw the specified node."""
        painter.setBrush(
            QBrush(
                self.selected_color
                if node is self.selected_node
                else self.regular_node_color,
                Qt.SolidPattern,
            )
        )

        node_position = node.get_position()
        node_radius = Vector(node.get_radius()).repeat(2)

        painter.drawEllipse(QPointF(*node_position), *node_radius)

        if self.labels_checkbox.isChecked():
            label = node.get_label()

            # scale font down, depending on the length of the label of the node
            painter.setFont(QFont(self.font_family, self.font_size / len(label)))

            # draw the node label within the node dimensions
            painter.drawText(
                QRectF(*(node_position - node_radius), *(2 * node_radius)),
                Qt.AlignCenter,
                label,
            )

    def draw_vertex(self, n1: Node, n2: Node, weight: float, painter):
        """Draw the specified vertex."""
        # special case for a node pointing to itself
        if n1 is n2:
            r = n1.get_radius()
            x, y = n1.get_position()

            painter.setPen(QPen(Qt.black, Qt.SolidLine))
            painter.setBrush(QBrush(Qt.black, Qt.NoBrush))

            painter.drawEllipse(QPointF(x - r / 2, y - r), r / 2, r / 2)

            head = Vector(x, y) - Vector(0, r)
            uv = Vector(0, 1)

            painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
            painter.drawPolygon(
                QPointF(*head),
                QPointF(*(head + (-uv).rotated(radians(10)) * self.arrowhead_size)),
                QPointF(*(head + (-uv).rotated(radians(-50)) * self.arrowhead_size)),
            )
        else:
            start, end = self.get_vertex_position(n1, n2)

            # draw the head of a directed arrow, which is an equilateral triangle
            if self.graph.is_directed():
                uv = (end - start).unit()

                painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
                painter.drawPolygon(
                    QPointF(*end),
                    QPointF(*(end + (-uv).rotated(radians(30)) * self.arrowhead_size)),
                    QPointF(*(end + (-uv).rotated(radians(-30)) * self.arrowhead_size)),
                )

            painter.setPen(QPen(Qt.black, Qt.SolidLine))
            painter.drawLine(QPointF(*start), QPointF(*end))

        if self.graph.is_weighted():
            # set color according to whether the vertex is selected or not
            painter.setBrush(
                QBrush(
                    self.selected_color
                    if self.selected_vertex is not None
                    and (
                        (
                            n1 is self.selected_vertex[0]
                            and n2 is self.selected_vertex[1]
                        )
                        or (
                            not self.graph.is_directed()
                            and n2 is self.selected_vertex[0]
                            and n1 is self.selected_vertex[1]
                        )
                    )
                    else self.regular_vertex_weight_color,
                    Qt.SolidPattern,
                )
            )

            weight_rectangle = self.get_vertex_weight_rect(n1, n2, weight)
            painter.drawRect(weight_rectangle)

            painter.setFont(QFont(self.font_family, self.font_size / 3))

            painter.setPen(QPen(Qt.white, Qt.SolidLine))
            painter.drawText(weight_rectangle, Qt.AlignCenter, str(weight))
            painter.setPen(QPen(Qt.black, Qt.SolidLine))

    def get_vertex_position(self, n1: Node, n2: Node) -> Tuple[Vector, Vector]:
        """Return the position of the vertex on the screen."""
        # positions of the nodes
        n1_p = Vector(*n1.get_position())
        n2_p = Vector(*n2.get_position())

        # unit vector from n1 to n2
        uv = (n2_p - n1_p).unit()

        # start and end of the vertex to be drawn
        start = n1_p + uv * n1.get_radius()
        end = n2_p - uv * n2.get_radius()

        if self.graph.is_directed():
            # if the graph is directed and a vertex exists that goes the other way, we
            # have to move the start end end so the vertexes don't overlap
            if self.graph.does_vertex_exist(n2, n1):
                start = start.rotated(self.arrow_separation, n1_p)
                end = end.rotated(-self.arrow_separation, n2_p)

        return start, end

    def get_vertex_weight_rect(self, n1: Node, n2: Node, weight: float):
        """Get a RectF surrounding the weight of the node."""
        r = self.weight_rectangle_size

        # width adjusted to number of chars in weight label
        adjusted_width = len(str(weight)) / 3 * r + r / 3
        weight_vector = Vector(r if adjusted_width <= r else adjusted_width, r)

        if n1 is n2:
            # special case for a vertex pointing to itself
            mid = n1.get_position() - Vector(r * 3, r * 4)
        else:
            start, end = self.get_vertex_position(n1, n2)
            mid = (start + end) / 2

        return QRectF(*(mid - weight_vector), *(2 * weight_vector))


app = QApplication(sys.argv)
ex = TreeVisualizer()
sys.exit(app.exec_())
