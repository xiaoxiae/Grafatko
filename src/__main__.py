import sys
from math import sqrt

from PyQt5.QtCore import Qt, QSize, QTimer, QPoint
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame


class Node:
    """A class for working with physical representations of nodes in a graph."""

    def __init__(self, x, y, parent, radius=20):
        """Initializes a new node."""
        # coordinates of the graph on the board
        self.x, self.y = x, y

        # list of neighbours and radius
        self.neighbours = [] if parent is None else [parent]
        self.radius = radius

        # the list of forces acting on the node
        self.forces = []

    def add_force(self, force):
        """Adds a force that is acting upon the node to the force list."""
        self.forces.append(force)

    def evaluate_forces(self):
        """Evaluates all of the forces acting upon the node, moving it accordingly."""
        xd, yd = 0, 0
        while len(self.forces) != 0:
            force = self.forces.pop()
            xd += force[0]
            yd += force[1]

        self.x += xd
        self.y += yd


class TreeVisualizer(QWidget):

    def __init__(self):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        # simulation variables
        self.nodes = []
        self.selected_node = None

        # functions for calculating forces
        self.repulsion_force_function = lambda x: 1 / x * 10
        self.attraction_force_function = lambda x, d: 0 if x <= d else -(x - d) / 10

        # offset of the mouse from the position of the currently dragged node
        self.mouse_drag_offset = None

        # position of the mouse; is updated when the mouse moves
        self.mouse_x = -1
        self.mouse_y = -1

        # TIMERS
        self.simulation_timer = QTimer(interval=16, timeout=self.perform_simulation_iteration)

        # WIDGETS
        self.canvas = QFrame(self, minimumSize=QSize(600, 600))

        # WIDGET LAYOUT
        self.main_v_layout = QVBoxLayout(self, margin=0)
        self.main_v_layout.addWidget(self.canvas)

        self.setLayout(self.main_v_layout)

        # WINDOW SETTINGS
        self.setWindowTitle('Tree Visualizer in PyQt5!')
        self.setFont(QFont("Fira Code", 16))
        self.show()

        # start the simulation
        self.simulation_timer.start()

    def mousePressEvent(self, event):
        """Is called when a mouse button is pressed; creates and moves nodes/vertices."""
        x = event.pos().x()
        y = event.pos().y()

        # (potentially) find a node that has been pressed
        pressed_node = None
        for node in self.nodes:
            if self.distance(x, y, node.x, node.y) <= node.radius:
                pressed_node = node
                break

        # select/move node on left click; create new node/make a new connection on right click
        if event.button() == Qt.LeftButton:
            if pressed_node is not None:
                self.selected_node = pressed_node

                self.mouse_drag_offset = (x - self.selected_node.x,
                                          y - self.selected_node.y)
                self.mouse_x = x
                self.mouse_y = y
        else:
            # either make/remove a connection, or create a new node
            if pressed_node is not None:
                if pressed_node is not self.selected_node:
                    # if a connection does not exist between the nodes, create it; otherwise remove it
                    if pressed_node not in self.selected_node.neighbours:
                        pressed_node.neighbours.append(self.selected_node)
                        self.selected_node.neighbours.append(pressed_node)
                    else:
                        pressed_node.neighbours.remove(self.selected_node)
                        self.selected_node.neighbours.remove(pressed_node)
            else:
                # create a new node, with the parent being the currently selected node
                node = Node(x, y, self.selected_node)

                # if there is a node selected, add the newly created node as its neighbour
                if self.selected_node is not None:
                    self.selected_node.neighbours.append(node)

                # make the newly created node the currently selected node and add it to the list of nodes
                self.selected_node = node
                self.nodes.append(node)

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released; stops the drag."""
        self.mouse_drag_offset = None

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window; updates mouse coordiantes."""
        self.mouse_x = event.pos().x()
        self.mouse_y = event.pos().y()

    def perform_simulation_iteration(self):
        """Performs one iteration of the simulation."""
        # evaluate forces that act upon the nodes
        for i in range(len(self.nodes)):
            n1 = self.nodes[i]
            for j in range(i + 1, len(self.nodes)):
                n2 = self.nodes[j]

                # calculate the distance of the nodes and their normalized vectors
                d = self.distance(n1.x, n1.y, n2.x, n2.y)
                nx, ny = (n2.x - n1.x) / d, (n2.y - n1.y) / d

                # the size of the repel force between the two nodes
                fr = self.repulsion_force_function(d)

                # add the repel force to each of the nodes
                n1.add_force((-nx * fr, -ny * fr))
                n2.add_force((nx * fr, ny * fr))

                # if they are connected, add the leash force
                if n1 in n2.neighbours:
                    # the size of the repel force between the two nodes
                    fa = self.attraction_force_function(d, 70)

                    # add the repel force to each of the nodes
                    n1.add_force((-nx * fa, -ny * fa))
                    n2.add_force((nx * fa, ny * fa))

            # since this node will not be visited again, evaluate the forces
            n1.evaluate_forces()

        if self.selected_node is not None and self.mouse_drag_offset is not None:
            self.selected_node.x = self.mouse_x - self.mouse_drag_offset[0]
            self.selected_node.y = self.mouse_y - self.mouse_drag_offset[1]

        self.update()

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        # draw vertices; has to be drawn before nodes, so they aren't drawn on top of them
        for node in self.nodes:
            for neighbour in node.neighbours:
                painter.drawLine(node.x, node.y, neighbour.x, neighbour.y)

        # draw nodes
        for node in self.nodes:
            # selected nodes are red; others are white
            if node is self.selected_node:
                painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

            painter.drawEllipse(QPoint(node.x, node.y), node.radius, node.radius)

    def distance(self, x1, y1, x2, y2):
        """Returns the distance of two points in space."""
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


app = QApplication(sys.argv)
ex = TreeVisualizer()
sys.exit(app.exec_())
