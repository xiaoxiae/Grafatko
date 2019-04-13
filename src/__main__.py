import sys
from math import sqrt, cos, sin, radians

from PyQt5.QtCore import Qt, QSize, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QCheckBox, QHBoxLayout, QLineEdit, \
    QPushButton, QMessageBox

from graph import Graph


class TreeVisualizer(QWidget):

    def __init__(self):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        # graph variables
        self.graph = Graph()
        self.selected_node = None

        # offset of the mouse from the position of the currently dragged node
        self.mouse_drag_offset = None

        # position of the mouse; is updated when the mouse moves
        self.mouse_x = -1
        self.mouse_y = -1

        # variables for visualizing the graph
        self.node_radius = 20
        self.arrowhead_size = 4

        self.selected_node_color = Qt.red
        self.regular_node_color = Qt.white

        self.word_limit = 10  # limit the displayed length of words for each node

        # UI variables
        self.font_family = "Fira Code"
        self.font_size = 18

        # canvas positioning - scale and translation
        self.scale = 1
        self.scale_coefficient = 1.1  # by how much the scale changes on scroll
        self.translation = [0, 0]

        # for moving the nodes
        self.node_rotation_angle = 20

        # TIMERS
        # runs the simulation 60 times a second (1000/60 ~= 16ms)
        self.simulation_timer = QTimer(interval=16, timeout=self.perform_simulation_iteration)

        # WIDGETS
        self.canvas = QFrame(self, minimumSize=QSize(600, 600))

        # for toggling between oriented/unoriented graphs
        self.oriented_checkbox = QCheckBox(text="oriented", clicked=self.set_graph_orientation)

        # for editing the labels of the nodes
        self.labels_checkbox = QCheckBox(text="labels")
        self.labels_line_edit = QLineEdit(enabled=self.labels_checkbox.isChecked(),
                                          textChanged=self.update_selected_node_label)

        # for displaying information about the app
        self.about_button = QPushButton(text="?", clicked=self.show_help)

        # WIDGET LAYOUT
        self.main_v_layout = QVBoxLayout(self, margin=0)
        self.main_v_layout.addWidget(self.canvas)

        self.option_h_layout = QHBoxLayout(self, margin=10)
        self.option_h_layout.addWidget(self.oriented_checkbox)
        self.option_h_layout.addWidget(self.labels_checkbox)
        self.option_h_layout.addWidget(self.labels_line_edit)
        self.option_h_layout.addWidget(self.about_button)

        self.main_v_layout.addLayout(self.option_h_layout)

        self.setLayout(self.main_v_layout)

        # WINDOW SETTINGS
        self.setWindowTitle('Graph Visualizer')
        self.setFont(QFont(self.font_family, self.font_size))
        self.show()

        # start the simulation
        self.simulation_timer.start()

    def repulsion_force(self, distance):
        """Calculates the strength of the repulsion force at the specified distance."""
        return 1 / distance * 10

    def attraction_force(self, distance, leash_length=80):
        """Calculates the strength of the attraction force at the specified distance and leash length."""
        return -(distance - leash_length) / 10

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
            <li><em>Right Mouse Button</em> &ndash; creates new nodes and vertices from the currently selected node</li>
            <li><em>Mouse Wheel</em> &ndash; zooms in/out</li>
            <li><em>Shift + Mouse Wheel</em> &ndash; rotates all of the nodes around the currently selected node<br /></li>
            <li><em>Delete</em> &ndash; deletes the currently selected node</li>
            </ul>
            <hr />
            <p>If you spot an issue, or would like to check out the source code, see the app's 
            <a href="https://github.com/xiaoxiae/GraphVisualizer">GitHub repository</a>.</p>
        """

        QMessageBox.information(self, "About", message)

    def set_graph_orientation(self):
        """Is called when the oriented checkbox changes; sets the orientation of the graph."""
        self.graph.set_oriented(self.oriented_checkbox.isChecked())

    def update_selected_node_label(self, text):
        """Is called when the labels line edit changes; changes the label of the currently selected node. If the label
        exceeds the maximum displayed length of a node, turns the labels line edit red."""
        self.selected_node.set_label(text)

        # set the background of the line edit color, according to whether the word is of appropriate length
        palette = self.labels_line_edit.palette()
        if len(text) > self.word_limit:
            palette.setColor(self.labels_line_edit.backgroundRole(), Qt.red)
        else:
            palette.setColor(self.labels_line_edit.backgroundRole(), Qt.white)
        self.labels_line_edit.setPalette(palette)

    def select_node(self, node):
        """Sets the selected node to the specified node, changes the text in labels line edit to its label and
        enables it."""
        self.selected_node = node
        self.labels_line_edit.setText(node.get_label())
        self.labels_line_edit.setEnabled(True)

    def deselect_node(self):
        """Sets the selected node to None and disables the labels line edit."""
        self.selected_node = None
        self.labels_line_edit.setEnabled(False)

    def keyPressEvent(self, event):
        """Is called when a key is pressed on the keyboard; deletes vertices."""
        if event.key() == Qt.Key_Delete:
            if self.selected_node is not None:
                self.graph.delete_node(self.selected_node)
                self.deselect_node()

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

        # select/move node on left click
        # create new node/make a new connection on right click
        if event.button() == Qt.LeftButton:
            if pressed_node is not None:
                # select and move the node if it isn't already selected; else de-select it
                self.select_node(pressed_node)

                self.mouse_drag_offset = (x - self.selected_node.get_x(), y - self.selected_node.get_y())
                self.mouse_x = x
                self.mouse_y = y
            else:
                self.deselect_node()
        elif event.button() == Qt.RightButton:
            # either make/remove a connection, or create a new node
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
        """Is called when a mouse button is released; stops the drag."""
        self.mouse_drag_offset = None

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window; updates mouse coordinates."""
        mouse_coordinates = self.get_mouse_coordinates(event, scale_down=True)

        self.mouse_x = mouse_coordinates[0]
        self.mouse_y = mouse_coordinates[1]

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; controls the zoom and node rotation."""
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            if self.selected_node is not None:
                # positive/negative for scrolling away and towards the user
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

            # adjust translation so the x and y of the mouse remains the same
            scale_delta = self.scale - prev_scale
            self.translation[0] += -(x * scale_delta)
            self.translation[1] += -(y * scale_delta)

    def rotate_nodes_around(self, x, y, angle):
        """Rotates coordinates of all of the points by a certain angle (in degrees) around the specified point."""
        angle = radians(angle)

        for node in self.graph.get_nodes():
            if node is not self.selected_node:
                # translate the coordinates to origin for the rotation to work
                node_x, node_y = node.get_x() - x, node.get_y() - y

                # rotate and translate the coordinates of the node
                node.set_x(node_x * cos(angle) - node_y * sin(angle) + x)
                node.set_y(node_x * sin(angle) + node_y * cos(angle) + y)

    def get_mouse_coordinates(self, event, scale_down=False):
        """Returns mouse coordinates if they are within the canvas and None if they are not. If scale_down is True, the
        function will scale down the coordinates to be within the canvas (useful for dragging) and return them."""
        x = event.pos().x()
        y = event.pos().y()

        # whether the coordinate components are on canvas
        x_on_canvas = 0 <= x <= self.canvas.width()
        y_on_canvas = 0 <= y <= self.canvas.height()

        # return if scale_down is True, scale down the coordinates so they're on canvas
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

                # if they are connected, add the leash force, regardless of whether the graph is oriented or not
                if self.graph.does_vertex_exist(n1, n2, ignore_orientation=True):
                    # the size of the attraction force between the two nodes
                    fa = self.attraction_force(d)

                    # add the repel force to each of the nodes, in the opposite directions
                    n1.add_force((-ux * fa, -uy * fa))
                    n2.add_force((ux * fa, uy * fa))

            # since this node will not be visited again, evaluate the forces
            n1.evaluate_forces()

        # drag the selected node
        if self.selected_node is not None and self.mouse_drag_offset is not None:
            self.selected_node.set_x(self.mouse_x - self.mouse_drag_offset[0])
            self.selected_node.set_y(self.mouse_y - self.mouse_drag_offset[1])

        self.update()

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        # bound the area to only draw on canvas
        painter.setClipRect(0, 0, self.canvas.width(), self.canvas.height())

        # draw the background
        painter.drawRect(0, 0, self.canvas.width(), self.canvas.height())

        # reposition the painter
        painter.translate(self.translation[0], self.translation[1])
        painter.scale(self.scale, self.scale)

        # draw vertices; has to be drawn before nodes, so they aren't drawn on top of them
        for node in self.graph.get_nodes():
            for neighbour in node.get_neighbours():
                x1, y1, x2, y2 = node.get_x(), node.get_y(), neighbour.get_x(), neighbour.get_y()

                # if it's oriented, draw an arrow
                if self.graph.is_oriented():
                    # calculate the position of the head of the arrow
                    # done by "shrinking" the distance from (x1, y1) to (x2, y2) by the radius of the node at (x2, y2)
                    d = self.distance(x1, y1, x2, y2)
                    ux, uy = (x2 - x1) / d, (y2 - y1) / d
                    r = neighbour.get_radius()

                    # the position of the head of the arrow
                    xa, ya = x1 + ux * (d - r), y1 + uy * (d - r)

                    # calculate the base of the arrow
                    # this is done the same way as the previous calculation
                    d = self.distance(x1, y1, xa, ya)
                    ux, uy = (xa - x1) / d, (ya - y1) / d

                    # position of the base of the arrow
                    x, y = x1 + ux * (d - self.arrowhead_size * 2), y1 + uy * (d - self.arrowhead_size * 2)

                    # the normal vectors to the unit vector of the arrow head
                    nx, ny = -uy, ux

                    painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
                    painter.drawPolygon(QPoint(xa, ya),
                                        QPoint(x + nx * self.arrowhead_size, y + ny * self.arrowhead_size),
                                        QPoint(x - nx * self.arrowhead_size, y - ny * self.arrowhead_size))

                painter.drawLine(x1, y1, x2, y2)

        # draw nodes
        for node in self.graph.get_nodes():
            # selected nodes are red to make them distinct; others are white
            if node is self.selected_node:
                painter.setBrush(QBrush(self.selected_node_color, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(self.regular_node_color, Qt.SolidPattern))

            # information about the node necessary for drawing
            x, y, r = node.get_x(), node.get_y(), node.get_radius()

            painter.drawEllipse(QPoint(x, y), r, r)

            # only draw labels if the label checkbox is checked
            if self.labels_checkbox.isChecked():
                label = node.get_label()[:self.word_limit]

                # only draw the label, if it has characters
                if len(label) != 0:
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
