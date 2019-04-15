import sys
from math import sqrt, cos, sin, radians, pi
from random import random

from PyQt5.QtCore import Qt, QSize, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QCheckBox, QHBoxLayout, QLineEdit, \
    QPushButton, QMessageBox, QFileDialog, QSizePolicy

from graph import Graph


class TreeVisualizer(QWidget):

    def __init__(self):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        # graph variables
        self.graph = Graph()
        self.selected_node = None

        self.vertex_positions = []
        self.selected_vertex = None

        # offset of the mouse from the position of the currently dragged node
        self.mouse_drag_offset = None

        # position of the mouse; is updated when the mouse moves
        self.mouse_x = -1
        self.mouse_y = -1

        # variables for visualizing the graph
        self.node_radius = 20
        self.weight_rectangle_size = self.node_radius / 3

        self.arrowhead_size = 4
        self.arrow_separation = pi / 7

        self.selected_color = Qt.red
        self.regular_node_color = Qt.white
        self.regular_vertex_weight_color = Qt.black

        # limit the displayed length of labels for each node
        self.node_label_limit = 10

        # UI variables
        self.font_family = "Times New Roman"
        self.font_size = 18

        self.layout_margins = 8
        self.layout_item_spacing = 2 * self.layout_margins

        # canvas positioning - scale and translation
        self.scale = 1
        self.scale_coefficient = 1.1  # by how much the scale changes on scroll
        self.translation = [0, 0]

        # angle (in degrees) by which all of the nodes rotate
        self.node_rotation_angle = 15

        # TIMERS
        # runs the simulation 60 times a second (1000/60 ~= 16ms)
        self.simulation_timer = QTimer(interval=16, timeout=self.perform_simulation_iteration)

        # WIDGETS
        self.canvas = QFrame(self, minimumSize=QSize(0, 400))
        self.canvas_size = None
        self.canvas.resizeEvent = self.adjust_canvas_translation

        # toggles between directed/undirected graphs
        self.directed_toggle_button = QPushButton(text="undirected", clicked=self.toggle_directed_graph)

        # for showing the labels of the nodes
        self.labels_checkbox = QCheckBox(text="labels")

        # sets, whether the graph is weighted or not
        self.weighted_checkbox = QCheckBox(text="weighted", clicked=self.set_weighted_graph)

        # enables/disables forces (True by default - they're fun!)
        self.forces_checkbox = QCheckBox(text="forces", checked=True)

        # input of the labels and vertex weights
        self.input_line_edit = QLineEdit(enabled=self.labels_checkbox.isChecked(),
                                         textChanged=self.input_line_edit_changed)

        # displays information about the app
        self.about_button = QPushButton(text="?", clicked=self.show_help,
                                        sizePolicy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

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

        self.io_h_layout = QHBoxLayout(self, margin=self.layout_margins)
        self.io_h_layout.addWidget(self.import_graph_button)
        self.io_h_layout.addSpacing(self.layout_item_spacing)
        self.io_h_layout.addWidget(self.export_graph_button)
        self.io_h_layout.addSpacing(self.layout_item_spacing)
        self.io_h_layout.addWidget(self.about_button)

        self.main_v_layout.addLayout(self.option_h_layout)
        self.main_v_layout.addSpacing(-self.layout_margins)
        self.main_v_layout.addLayout(self.io_h_layout)

        self.setLayout(self.main_v_layout)

        # WINDOW SETTINGS
        self.setWindowTitle('Graph Visualizer')
        self.setFont(QFont(self.font_family, self.font_size))
        self.setWindowIcon(QIcon("icon.ico"))
        self.show()

        # start the simulation
        self.simulation_timer.start()

    def set_weighted_graph(self):
        """Is called when the weighted checkbox is pressed; sets, whether the graph is weighted or not."""
        self.graph.set_weighted(self.weighted_checkbox.isChecked())

    def adjust_canvas_translation(self, event):
        """Is called when the canvas widget is resized; changes translation so the center stays in the center."""
        size = (event.size().width(), event.size().height())

        # don't translate on the initial resize
        if self.canvas_size is not None:
            self.translation[0] += self.scale * (size[0] - self.canvas_size[0]) / 2
            self.translation[1] += self.scale * (size[1] - self.canvas_size[1]) / 2

        self.canvas_size = size

    def repulsion_force(self, distance):
        """Calculates the strength of the repulsion force at the specified distance."""
        return 1 / distance * 10 if self.forces_checkbox.isChecked() else 0

    def attraction_force(self, distance, leash_length=80):
        """Calculates the strength of the attraction force at the specified distance and leash length."""
        return -(distance - leash_length) / 10 if self.forces_checkbox.isChecked() else 0

    def import_graph(self):
        """Is called when the import button is clicked; imports a graph from a file."""
        path = QFileDialog.getOpenFileName()[0]

        if path != "":
            try:
                with open(path, "r") as file:
                    # a list of vertices of the graph
                    data = [line.strip() for line in file.read().splitlines()]

                    sample = data[0].split(" ")
                    vertex_types = ["->", "<", "<>"]

                    # whether the graph is directed and weighted; done by looking at a sample input vertex
                    directed = True if sample[1] in vertex_types else False
                    weighted = False if len(sample) == 2 or directed and len(sample) == 3 else True

                    graph = Graph(directed=directed, weighted=weighted)

                    # to remember the created nodes and to connect them later
                    node_dictionary = {}

                    # add each of the nodes of the vertex to the graph
                    for vertex in data:
                        vertex_components = vertex.split(" ")

                        # the formats are either 'A B' or 'A ... B', where ... is one of the vertex types
                        nodes = [
                            vertex_components[0],
                            vertex_components[2] if directed else vertex_components[1]
                        ]

                        # if weights are present, the formats are either 'A B num' or 'A ... B num (num)'
                        weights_strings = None if not weighted else [
                            vertex_components[2] if not directed else vertex_components[3],
                            None if not directed or vertex_components[1] != vertex_types[2] else vertex_components[4]
                        ]

                        for node in nodes:
                            if node not in node_dictionary:
                                # slightly randomize the coordinates so the graph doesn't stay in one place
                                x = self.canvas.width() / 2 + (random() - 0.5)
                                y = self.canvas.height() / 2 + (random() - 0.5)

                                # add it to graph with default values
                                node_dictionary[node] = graph.add_node(x, y, self.node_radius, node)

                        # get the node objects from the names
                        n1, n2 = node_dictionary[nodes[0]], node_dictionary[nodes[1]]

                        # export the graph, according to the direction of the vertex, and whether it's weighted or not
                        if not directed or vertex_components[1] == "->":
                            if weighted:
                                graph.add_vertex(n1, n2, self._convert_string_to_number(weights_strings[0]))
                            else:
                                graph.add_vertex(n1, n2)
                        elif vertex_components[1] == "<-":
                            if weighted:
                                graph.add_vertex(n2, n1, self._convert_string_to_number(weights_strings[0]))
                            else:
                                graph.add_vertex(n2, n1)
                        else:
                            if weighted:
                                graph.add_vertex(n1, n2, self._convert_string_to_number(weights_strings[0]))
                                graph.add_vertex(n2, n1, self._convert_string_to_number(weights_strings[1]))
                            else:
                                graph.add_vertex(n1, n2)
                                graph.add_vertex(n2, n1)

                self.graph = graph

            except UnicodeDecodeError:
                QMessageBox.critical(self, "Error!", "Can't read binary files!")
            except ValueError:
                QMessageBox.critical(self, "Error!", "The weights of the graph are not numbers!")
            except Exception:
                QMessageBox.critical(self, "Error!", "An error occurred when importing the graph. Make sure that the "
                                                     "file is in the correct format!")

            # make sure that the UI is in order
            self.deselect_node()
            self.deselect_vertex()
            self.set_checkbox_values()

    def _convert_string_to_number(self, str):
        """Attempts to convert the specified string to a number. Throws error if it fails to do so!"""
        try:
            return int(str)
        except ValueError:
            return float(str)

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
                    for i in range(len(self.graph.get_nodes())):
                        n1 = self.graph.get_nodes()[i]
                        for j in range(i + 1, len(self.graph.get_nodes())):
                            n2 = self.graph.get_nodes()[j]

                            v1_exists = self.graph.does_vertex_exist(n1, n2)

                            w1_value = self.graph.get_weight(n1, n2)
                            w1 = "" if not self.graph.is_weighted() or w1_value is None else str(w1_value)

                            if not self.graph.is_directed() and v1_exists:
                                # for undirected graphs, no direction symbols are necessary
                                file.write(n1.get_label() + " " + n2.get_label() + " " + w1 + "\n")
                            else:
                                v2_exists = self.graph.does_vertex_exist(n2, n1)

                                w2_value = self.graph.get_weight(n2, n1)
                                w2 = "" if not self.graph.is_weighted() or w2_value is None else str(w2_value)

                                # node that w1 and w2 might be empty strings, so we can combine
                                # directed weighted and unweighted graphs in one command
                                if v1_exists and v2_exists:
                                    file.write("%s <> %s %s %s\n" % (n1.get_label(), n2.get_label(), str(w1), str(w2)))
                                elif v1_exists:
                                    file.write("%s -> %s %s\n" % (n1.get_label(), n2.get_label(), str(w1)))
                                elif v2_exists:
                                    file.write("%s <- %s %s\n" % (n1.get_label(), n2.get_label(), str(w2)))
            except Exception:
                QMessageBox.critical(self, "Error!", "An error occurred when exporting the graph. Make sure that you "
                                                     "have permission to write to the specified file and try again!")

    def show_help(self):
        """Is called when the help button is clicked; displays basic information about the application."""
        message = """
            <p>Welcome to <strong>Graph Visualizer</strong>.</p>
            <p>The app aims to help with creating, visualizing and exporting graphs. 
            It is powered by PyQt5 &ndash; a set of Python bindings for the C++ library Qt.</p>
            <hr />
            <p>The controls are as follows:</p>
            <ul>
            <li><em>Left Mouse Button</em> &ndash; selects nodes and moves them around</li>
            <li><em>Right Mouse Button</em> &ndash; creates new nodes and vertices</li>
            <li><em>Mouse Wheel</em> &ndash; zooms in/out</li>
            <li><em>Shift + Left Mouse Button</em> &ndash; moves connected nodes</li>
            <li><em>Shift + Mouse Wheel</em> &ndash; rotates nodes around the selected node<br /></li>
            <li><em>Escape</em> &ndash; deletes the currently selected node</li>
            </ul>
            <hr />
            <p>If you spot an issue, or would like to check out the source code, see the app's 
            <a href="https://github.com/xiaoxiae/GraphVisualizer">GitHub repository</a>.</p>
        """

        QMessageBox.information(self, "About", message)

    def toggle_directed_graph(self):
        """Is called when the directed checkbox changes; toggles between directed and undirected graphs."""
        self.graph.set_directed(not self.graph.is_directed())
        self.update_directed_toggle_button_text()

    def update_directed_toggle_button_text(self):
        """Changes the text of the directed toggle button, according to whether the graph is directer or not."""
        self.directed_toggle_button.setText("directed" if self.graph.is_directed() else "undirected")

    def input_line_edit_changed(self, text):
        """Is called when the input line edit changes; changes either the label of the node selected node, or the value
        of the selected vertex."""
        palette = self.input_line_edit.palette()

        if self.selected_node is not None:
            # the text has to be non-zero and not contain spaces, for the import/export language to work properly
            # the text length is also restricted, for rendering purposes
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

            # if the parsing was unsuccessful, set the input line edit background to red to indicate this fact
            # if it worked, set the weight by adding a new vertex with the input weight
            if weight is None:
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.red)
            else:
                self.graph.add_vertex(self.selected_vertex[0], self.selected_vertex[1], weight)
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.white)

        self.input_line_edit.setPalette(palette)

    def select_node(self, node):
        """Sets the selected node to the specified node, sets the input line edit to its label and enables it."""
        self.selected_node = node

        self.input_line_edit.setText(node.get_label())
        self.input_line_edit.setEnabled(True)
        self.input_line_edit.setFocus()

    def deselect_node(self):
        """Sets the selected node to None and disables the input line edit."""
        self.selected_node = None
        self.input_line_edit.setEnabled(False)

    def select_vertex(self, vertex):
        """Sets the selected vertex to the specified vertex, sets the input line edit to its weight and enables it."""
        self.selected_vertex = vertex

        self.input_line_edit.setText(str(self.graph.get_weight(*vertex)))
        self.input_line_edit.setEnabled(True)
        self.input_line_edit.setFocus()

    def deselect_vertex(self):
        """Sets the selected vertex to None and disables the input line edit."""
        self.selected_vertex = None
        self.input_line_edit.setEnabled(False)

    def keyPressEvent(self, event):
        """Is called when a key is pressed on the keyboard; deletes vertices."""
        if event.key() == Qt.Key_Escape:
            if self.selected_node is not None:
                self.graph.remove_node(self.selected_node)
                self.deselect_node()
            if self.selected_vertex is not None:
                self.graph.remove_vertex(self.selected_vertex[0], self.selected_vertex[1])
                self.deselect_vertex()

    def mousePressEvent(self, event):
        """Is called when a mouse button is pressed; creates and moves nodes/vertices."""
        mouse_coordinates = self.get_mouse_coordinates(event)

        # if we are not on canvas, don't do anything
        if mouse_coordinates is None:
            return

        # sets the focus to the entire window, for the keypresses to register
        self.setFocus()

        x = mouse_coordinates[0]
        y = mouse_coordinates[1]

        # (potentially) find a node that has been pressed
        pressed_node = None
        for node in self.graph.get_nodes():
            if self.distance(x, y, node.get_x(), node.get_y()) <= node.get_radius():
                pressed_node = node
                break

        # (potentially) find a vertex that has been pressed
        pressed_vertex = None
        for vertex in self.vertex_positions:
            # vertex position items have the structure [x, y, (n1, n2)]
            if abs(vertex[0] - x) < self.weight_rectangle_size and abs(vertex[1] - y) < self.weight_rectangle_size:
                pressed_vertex = vertex[2]

        # select on left click
        # create/connect on right click
        if event.button() == Qt.LeftButton:
            # nodes have the priority in selection before vertices
            if pressed_node is not None:
                self.deselect_vertex()
                self.select_node(pressed_node)

                self.mouse_drag_offset = (x - self.selected_node.get_x(), y - self.selected_node.get_y())
                self.mouse_x = x
                self.mouse_y = y
            elif pressed_vertex is not None:
                self.deselect_node()
                self.select_vertex(pressed_vertex)
            else:
                self.deselect_node()
                self.deselect_vertex()
        elif event.button() == Qt.RightButton:
            # either make/remove a connection if we right clicked a node, or create a new node if we haven't
            if pressed_node is not None:
                if self.selected_node is not None and pressed_node is not self.selected_node:
                    # if a connection does not exist between the nodes, create it; otherwise remove it
                    if self.graph.does_vertex_exist(self.selected_node, pressed_node):
                        self.graph.remove_vertex(self.selected_node, pressed_node)
                    else:
                        self.graph.add_vertex(self.selected_node, pressed_node)
            else:
                node = self.graph.add_node(x, y, self.node_radius)

                # if a selected node exists, connect it to the newly created node
                if self.selected_node is not None:
                    self.graph.add_vertex(self.selected_node, node)

                self.select_node(node)

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released; stops node drag."""
        self.mouse_drag_offset = None

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window; updates mouse coordinates."""
        mouse_coordinates = self.get_mouse_coordinates(event, scale_down=True)

        self.mouse_x = mouse_coordinates[0]
        self.mouse_y = mouse_coordinates[1]

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; node rotation and zoom."""
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            if self.selected_node is not None:
                # positive/negative for scrolling away from/towards the user
                angle = self.node_rotation_angle if event.angleDelta().y() > 0 else -self.node_rotation_angle

                self.rotate_nodes_around(self.selected_node.get_x(), self.selected_node.get_y(), angle)
        else:
            mouse_coordinates = self.get_mouse_coordinates(event)

            # only do something, if we're working on canvas
            if mouse_coordinates is None:
                return

            x, y = mouse_coordinates[0], mouse_coordinates[1]
            prev_scale = self.scale

            # adjust the canvas scale, depending on the scroll direction
            # if angleDelta.y() is positive, scroll away (zoom out) from the user (and vice versa)
            if event.angleDelta().y() > 0:
                self.scale /= self.scale_coefficient
            else:
                self.scale *= self.scale_coefficient

            # adjust translation so the x and y of the mouse stay in the same spot
            scale_delta = self.scale - prev_scale
            self.translation[0] += -(x * scale_delta)
            self.translation[1] += -(y * scale_delta)

    def rotate_nodes_around(self, x, y, angle):
        """Rotates coordinates of all of the points by a certain angle (in degrees) around the specified point."""
        angle = radians(angle)

        for node in self.graph.get_nodes():
            # only rotate points that are in the same continuity set
            if self.graph.share_continuity_set(node, self.selected_node):
                # translate the coordinates to origin for the rotation to work
                node_x, node_y = node.get_x() - x, node.get_y() - y

                # rotate and translate the coordinates of the node
                node.set_x(node_x * cos(angle) - node_y * sin(angle) + x)
                node.set_y(node_x * sin(angle) + node_y * cos(angle) + y)

    def get_mouse_coordinates(self, event, scale_down=False):
        """Returns mouse coordinates if they are within the canvas and None if they are not.
        If scale_down is True, the function will scale down the coordinates to be within the canvas (useful for
        dragging) and return them instead."""
        x = event.pos().x()
        y = event.pos().y()

        # booleans for whether the coordinate components are on canvas
        x_on_canvas = 0 <= x <= self.canvas.width()
        y_on_canvas = 0 <= y <= self.canvas.height()

        # scale down the coordinates if scale_down is True, or return none if we are not on canvas
        if scale_down:
            x = x if x_on_canvas else 0 if x <= 0 else self.canvas.width()
            y = y if y_on_canvas else 0 if y <= 0 else self.canvas.height()
        elif not x_on_canvas or not y_on_canvas:
            return None

        # return the mouse coordinates, accounting for the translation and scale of the canvas
        return ((x - self.translation[0]) / self.scale,
                (y - self.translation[1]) / self.scale)

    def perform_simulation_iteration(self):
        """Performs one iteration of the simulation."""
        # evaluate forces that act upon each pair of nodes
        for i in range(len(self.graph.get_nodes())):
            n1 = self.graph.get_nodes()[i]
            for j in range(i + 1, len(self.graph.get_nodes())):
                n2 = self.graph.get_nodes()[j]

                # if they are not in the same continuity set, no forces act on them
                if not self.graph.share_continuity_set(n1, n2):
                    continue

                # calculate the distance of the nodes and a unit vector from the first to the second
                d = self.distance(n1.get_x(), n1.get_y(), n2.get_x(), n2.get_y())

                # if the nodes are right on top of each other, the force can't be calculated
                if d == 0:
                    continue

                ux, uy = (n2.get_x() - n1.get_x()) / d, (n2.get_y() - n1.get_y()) / d

                # the size of the repel force between the two nodes
                fr = self.repulsion_force(d)

                # add a repel force to each of the nodes, in the opposite directions
                n1.add_force((-ux * fr, -uy * fr))
                n2.add_force((ux * fr, uy * fr))

                # if they are connected, add the leash force, regardless of whether the graph is directed or not
                if self.graph.does_vertex_exist(n1, n2, ignore_direction=True):
                    # the size of the attraction force between the two nodes
                    fa = self.attraction_force(d)

                    # add the repel force to each of the nodes, in the opposite directions
                    n1.add_force((-ux * fa, -uy * fa))
                    n2.add_force((ux * fa, uy * fa))

            # since this node will not be visited again, evaluate the forces
            n1.evaluate_forces()

        # drag the selected node, after all of the forces have been applied, so it doesn't move anymore
        if self.selected_node is not None and self.mouse_drag_offset is not None:
            prev_x = self.selected_node.get_x()
            prev_y = self.selected_node.get_y()

            self.selected_node.set_x(self.mouse_x - self.mouse_drag_offset[0])
            self.selected_node.set_y(self.mouse_y - self.mouse_drag_offset[1])

            # move the rest of the nodes that are connected to the selected node, if shift is pressed
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                x_delta = self.selected_node.get_x() - prev_x
                y_delta = self.selected_node.get_y() - prev_y

                for node in self.graph.get_nodes():
                    if node is not self.selected_node and self.graph.share_continuity_set(node, self.selected_node):
                        node.set_x(node.get_x() + x_delta)
                        node.set_y(node.get_y() + y_delta)

        self.update()

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        # bound the canvas area to not draw outside of it
        painter.setClipRect(0, 0, self.canvas.width(), self.canvas.height())

        # draw the background
        painter.drawRect(0, 0, self.canvas.width(), self.canvas.height())

        # transform and scale the painter accordingly
        painter.translate(self.translation[0], self.translation[1])
        painter.scale(self.scale, self.scale)

        # if the graph is weighted, reset the positions, since they will be re-drawn later on
        if self.graph.is_weighted():
            self.vertex_positions = []

        # draw vertices; has to be drawn before nodes, so they aren't drawn on top of them
        for node in self.graph.get_nodes():
            for neighbour, weight in node.get_neighbours().items():
                x1, y1, x2, y2 = node.get_x(), node.get_y(), neighbour.get_x(), neighbour.get_y()

                # create a unit vector from the first to the second graph
                d = self.distance(x1, y1, x2, y2)
                ux, uy = (x2 - x1) / d, (y2 - y1) / d
                r = neighbour.get_radius()

                # if it's directed, draw the head of the arrow
                if self.graph.is_directed():
                    # in case there is a vertex going the other way, we will move the line up the circles by an angle,
                    # so there is separation between the vertices
                    if self.graph.does_vertex_exist(neighbour, node):
                        nx = -uy * r * sin(self.arrow_separation) + ux * r * (1 - cos(self.arrow_separation))
                        ny = ux * r * sin(self.arrow_separation) + uy * r * (1 - cos(self.arrow_separation))

                        x1, x2, y1, y2 = x1 + nx, x2 + nx, y1 + ny, y2 + ny

                    # the position of the head of the arrow
                    xa, ya = x1 + ux * (d - r), y1 + uy * (d - r)

                    # calculate the two remaining points of the arrow
                    # this is done the same way as the previous calculation (shift by vector)
                    d = self.distance(x1, y1, xa, ya)
                    ux_arrow, uy_arrow = (xa - x1) / d, (ya - y1) / d

                    # position of the base of the arrow
                    x, y = x1 + ux_arrow * (d - self.arrowhead_size * 2), y1 + uy_arrow * (d - self.arrowhead_size * 2)

                    # the normal vectors to the unit vector of the arrow head
                    nx_arrow, ny_arrow = -uy_arrow, ux_arrow

                    # draw the tip of the arrow, as the triangle
                    painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
                    painter.drawPolygon(QPoint(xa, ya),
                                        QPoint(x + nx_arrow * self.arrowhead_size, y + ny_arrow * self.arrowhead_size),
                                        QPoint(x - nx_arrow * self.arrowhead_size, y - ny_arrow * self.arrowhead_size))

                # draw only one of the two vertices, if the graph is undirected
                if self.graph.is_directed() or id(node) < id(neighbour):
                    painter.drawLine(x1, y1, x2, y2)

                    if self.graph.is_weighted():
                        x_middle, y_middle = (x2 + x1) / 2, (y2 + y1) / 2

                        # if the graph is directed, the vertices are offset (so they aren't draw on top of each other),
                        # so we need to shift them back to be at the midpoint between the nodes
                        if self.graph.is_directed():
                            x_middle -= ux * r * (1 - cos(self.arrow_separation))
                            y_middle -= uy * r * (1 - cos(self.arrow_separation))

                        r = self.weight_rectangle_size

                        self.vertex_positions.append((x_middle, y_middle, (node, neighbour)))

                        # make the selected vertex rectangle background different, if it's selected (for aesthetics)
                        if self.selected_vertex is not None and node is self.selected_vertex[0] and neighbour is \
                                self.selected_vertex[1]:
                            painter.setBrush(QBrush(self.selected_color, Qt.SolidPattern))
                        else:
                            painter.setBrush(QBrush(self.regular_vertex_weight_color, Qt.SolidPattern))

                        painter.drawRect(QRect(x_middle - r, y_middle - r, 2 * r, 2 * r))

                        # adjust the length of the weight string, so the minus sign doesn't make the number smaller
                        length = len(str(weight)) - (1 if weight < 0 else 0)

                        painter.setFont(QFont(self.font_family, self.font_size / (length * 3)))

                        # draw the value of the vertex (in white, so it's visible against the background)
                        painter.setPen(QPen(Qt.white, Qt.SolidLine))
                        painter.drawText(QRect(x_middle - r, y_middle - r, 2 * r, 2 * r), Qt.AlignCenter, str(weight))
                        painter.setPen(QPen(Qt.black, Qt.SolidLine))

        # draw nodes
        for node in self.graph.get_nodes():
            # selected nodes are red to make them distinct; others are white
            if node is self.selected_node:
                painter.setBrush(QBrush(self.selected_color, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(self.regular_node_color, Qt.SolidPattern))

            x, y, r = node.get_x(), node.get_y(), node.get_radius()

            painter.drawEllipse(QPoint(x, y), r, r)

            # only draw labels if the label checkbox is checked
            if self.labels_checkbox.isChecked():
                label = node.get_label()

                # scale font down, depending on the length of the label of the node
                painter.setFont(QFont(self.font_family, self.font_size / len(label)))

                # draw the node label within the node dimensions
                painter.drawText(QRect(x - r, y - r, 2 * r, 2 * r), Qt.AlignCenter, label)

    def distance(self, x1, y1, x2, y2):
        """Returns the distance of two points in space."""
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


app = QApplication(sys.argv)
ex = TreeVisualizer()
sys.exit(app.exec_())
