import sys
from math import sqrt

from PyQt5.QtCore import Qt, QSize, QTimer, QPoint
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame

from src.graph import Graph


class TreeVisualizer(QWidget):

    def __init__(self):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        # graph variables
        self.graph = Graph()
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
        for node in self.graph.get_nodes():
            if self.distance(x, y, node.get_x(), node.get_y()) <= node.get_radius():
                pressed_node = node
                break

        # select/move node on left click; create new node/make a new connection on right click
        if event.button() == Qt.LeftButton:
            if pressed_node is not None:
                self.selected_node = pressed_node

                self.mouse_drag_offset = (x - self.selected_node.get_x(), y - self.selected_node.get_y())
                self.mouse_x = x
                self.mouse_y = y
        else:
            # either make/remove a connection, or create a new node
            if pressed_node is not None:
                if pressed_node is not self.selected_node:
                    # if a connection does not exist between the nodes, create it; otherwise remove it
                    if self.graph.does_vertice_exist(pressed_node, self.selected_node):
                        self.graph.remove_vertice(pressed_node, self.selected_node)
                    else:
                        self.graph.add_vertice(pressed_node, self.selected_node)
            else:
                # create a new node
                node = self.graph.add_node(x, y)

                # if a selected node exists, connect it to the newly created node
                if self.selected_node is not None:
                    self.graph.add_vertice(node, self.selected_node)

                # make the newly created node the currently selected node
                self.selected_node = node

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
        for i in range(len(self.graph.get_nodes())):
            n1 = self.graph.get_nodes()[i]
            for j in range(i + 1, len(self.graph.get_nodes())):
                n2 = self.graph.get_nodes()[j]

                # calculate the distance of the nodes and their normalized vectors
                d = self.distance(n1.get_x(), n1.get_y(), n2.get_x(), n2.get_y())
                nx, ny = (n2.get_x() - n1.get_x()) / d, (n2.get_y() - n1.get_y()) / d

                # the size of the repel force between the two nodes
                fr = self.repulsion_force_function(d)

                # add the repel force to each of the nodes
                n1.add_force((-nx * fr, -ny * fr))
                n2.add_force((nx * fr, ny * fr))

                # if they are connected, add the leash force
                if self.graph.does_vertice_exist(n1, n2):
                    # the size of the repel force between the two nodes
                    fa = self.attraction_force_function(d, 70)

                    # add the repel force to each of the nodes
                    n1.add_force((-nx * fa, -ny * fa))
                    n2.add_force((nx * fa, ny * fa))

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

        # bound the area to only draw on the canvas
        painter.setClipRect(0, 0, self.canvas.width(), self.canvas.height())

        # draw vertices; has to be drawn before nodes, so they aren't drawn on top of them
        for node in self.graph.get_nodes():
            for neighbour in node.get_neighbours():
                painter.drawLine(node.get_x(), node.get_y(), neighbour.get_x(), neighbour.get_y())

        # draw nodes
        for node in self.graph.get_nodes():
            # selected nodes are red; others are white
            if node is self.selected_node:
                painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

            painter.drawEllipse(QPoint(node.get_x(), node.get_y()), node.get_radius(), node.get_radius())

    def distance(self, x1, y1, x2, y2):
        """Returns the distance of two points in space."""
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


app = QApplication(sys.argv)
ex = TreeVisualizer()
sys.exit(app.exec_())
