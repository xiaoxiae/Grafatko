import sys

# CLEAN CODE :)
from typing import *


# QT
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qtmodern import styles  # themes


# UTILITIES
from functools import partial
from random import random
from math import radians

from graph import *
from utilities import *
import webbrowser  # opening the browser


@dataclass
class Mouse:
    """A small class for storing information about the mouse."""

    position: Vector = None  # it position on canvas

    # offset of the mouse from the position of the currently dragged node
    drag_offset: Vector = None

    # if the appropriate button is pressed, the variables store where
    # used in dragging nodes around
    left_pressed: bool = None
    right_pressed: bool = None


class Canvas(QWidget):
    # WIDGET OPTIONS
    lighten_coefficient = 10  # how much lighter/darker the canvas is (to background)

    # positioning
    scale_coefficient: float = 8  # by how much the scale changes on scroll

    # whether the forces are enabled/disabled
    forces: bool = True

    # _ because self.repulsion gets self as the first argument
    repulsion = lambda _, distance: (1 / distance) ** 2
    attraction = lambda _, distance: -(distance - 8) / 10

    def __init__(self, parent=None):
        super().__init__(parent)

        # MOUSE
        self.setMouseTracking(True)

        self.scale: float = 10
        self.translation: float = Vector(0, 0)

        self.mouse = Mouse()

        # GRAPH
        self.graph = DrawableGraph()
        self.selected_nodes = None

        # timer that runs the simulation (60 times a second... once every ~= 17ms)
        QTimer(self, interval=17, timeout=self.update).start()

    def update(self, *args):
        """A function that gets periodically called to update the canvas."""
        # only move the nodes when forces are enabled
        if self.forces:
            for i, n1 in enumerate(self.graph.get_nodes()):
                for n2 in self.graph.get_nodes()[i + 1 :]:
                    # TODO: add weakly_connected check

                    d = n1.get_position().distance(n2.get_position())

                    # if they are on top of each other, nudge one of them slightly
                    if d == 0:
                        n1.add_force(Vector(random(), random()))
                        continue

                    # unit vector from n1 to n2
                    uv = (n2.get_position() - n1.get_position()).unit()

                    # the size of the repel force between the two nodes
                    fr = self.repulsion(d)

                    # add a repel force to each of the nodes, in the opposite directions
                    n1.add_force(-uv * fr)
                    n2.add_force(uv * fr)

                    # if they are also connected, add the attraction force
                    # the direction does not matter -- it would look weird for directed
                    if self.graph.is_vertex(n1, n2) or self.graph.is_vertex(n2, n1):
                        fa = self.attraction(d)

                        n1.add_force(-uv * fa)
                        n2.add_force(uv * fa)

                n1.evaluate_forces()

        # drag the selected nodes, if the left button is being held and dragged
        if self.selected_nodes is not None and self.mouse.left_pressed:
            # TODO: if shift is pressed, move by components

            for node in self.selected_nodes:
                node.set_position(self.mouse.position - self.mouse.drag_offset)

        super().update(*args)

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # clipping
        painter.setClipRect(0, 0, self.width(), self.height())

        # paint the background
        self.paint_background(painter)

        # translate the world
        painter.translate(*self.translation)
        painter.scale(self.scale, self.scale)

        # paint the graph
        self.graph.draw(painter, self.palette())

    def paint_background(self, painter: QPainter):
        """Paint the background of the widget."""
        # color shenanigans
        default_background = self.palette().color(QPalette.Background)

        background = default_background.lighter(100 + self.lighten_coefficient)
        border = default_background.darker(100 + self.lighten_coefficient)

        painter.setBrush(QBrush(background, Qt.SolidPattern))
        painter.setPen(QPen(border, Qt.SolidLine))

        # draw background
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window."""
        self.update_mouse(event)

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released."""
        self.update_mouse(event)

        if event.button() == Qt.LeftButton:
            self.mouse.left_pressed = False

        elif event.button() == Qt.RightButton:
            self.mouse.right_pressed = False

    def mousePressEvent(self, event):
        """Is called when a mouse button is released."""
        self.update_mouse(event)

        pressed_node = self.graph.node_at_position(self.mouse.position)

        if event.button() == Qt.LeftButton:
            self.mouse.left_pressed = True

            # if a node was pressed, select it
            if pressed_node is not None:
                self.select(pressed_node)

                self.mouse.drag_offset = (
                    self.mouse.position - pressed_node.get_position()
                )

            # else deselect 'em all
            else:
                self.deselect()

        elif event.button() == Qt.RightButton:
            self.mouse.right_pressed = True

            # if there isn't a node at the position, create a new one
            if pressed_node is None:
                # re-used to make the code shorter
                pressed_node = DrawableNode(self.mouse.position)

                self.graph.add_node(pressed_node)
                self.select(pressed_node)

            # if some nodes are selected, connect them to the pressed node
            if self.selected_nodes is not None:
                for selected_node in self.selected_nodes:
                    self.graph.add_vertex(selected_node, pressed_node)

    def update_mouse(self, event):
        """Update the position of the mouse on the canvas."""
        raw_position = Vector(event.pos().x(), event.pos().y())
        self.mouse.position = (raw_position - self.translation) / self.scale

    def select(self, node: DrawableNode):
        """Select the given node."""
        shift_pressed = QApplication.keyboardModifiers() == Qt.ShiftModifier

        if not shift_pressed or self.selected_nodes == None:
            self.selected_nodes = []

        self.selected_nodes.append(node)

    def deselect(self):
        """Deselect all nodes."""
        self.selected_nodes = None

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; node rotation and zoom."""
        # positive/negative for scrolling away from/towards the user
        scroll_distance = radians(event.angleDelta().y() / self.scale_coefficient)

        # adjust the scale
        previous_scale = self.scale
        self.scale *= 2 ** scroll_distance

        # adjust translation so the x and y of the mouse stay in the same spot
        self.translation -= self.mouse.position * (self.scale - previous_scale)

    def get_graph(self):
        """Get the current graph."""
        return self.graph

    def set_forces(self, value: bool):
        """Enable/disable the forces that act on the nodes."""
        self.forces = value


class GraphVisualizer(QMainWindow):
    def __init__(self):
        # TODO: command line argument parsing (--dark and stuff)
        # TODO: hide toolbar with f-10 or something

        super().__init__()

        # Widgets
        ## Canvas (main widget)
        self.canvas = Canvas(parent=self)
        self.canvas.setMinimumSize(100, 200)  # reasonable minimum size
        self.setCentralWidget(self.canvas)

        ## Top menu bar
        self.menubar = self.menuBar()

        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(QAction("&Import", self))
        self.file_menu.addAction(QAction("&Export", self))
        self.file_menu.addSeparator()
        self.file_menu.addAction(QAction("&Quit", self, triggered=exit))

        self.preferences_menu = self.menubar.addMenu("&Preferences")
        self.preferences_menu.addAction(
            QAction(
                "&Dark Theme",
                self,
                checkable=True,
                triggered=partial(
                    lambda x, y: styles.dark(x) if y else styles.light(x),
                    QApplication.instance(),
                ),
            )
        )

        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(QAction("&Manual", self))
        self.help_menu.addAction(QAction("&About", self))
        self.help_menu.addAction(
            QAction(
                "&Source Code",
                self,
                triggered=partial(
                    # TODO: make non-blocking
                    webbrowser.open,
                    "https://github.com/xiaoxiae/GraphVisualizer",
                ),
            )
        )

        ## Dock
        # TODO: shrink after leaving the dock
        # TODO: disable vertical resizing
        self.dock_menu = QDockWidget("Settings", self)
        self.dock_menu.setAllowedAreas(Qt.BottomDockWidgetArea)  # float bottom
        self.dock_menu.setFeatures(QDockWidget.DockWidgetFloatable)  # hide close button

        self.dock_widget = QWidget()
        layout = QGridLayout()

        ### Graph options
        layout.addWidget(QLabel(self, text="Graph"), 0, 0)

        layout.addWidget(
            QCheckBox(
                "directed",
                self,
                toggled=lambda value: self.canvas.get_graph().set_directed(value),
            ),
            1,
            0,
        )

        layout.addWidget(
            QCheckBox(
                "weighted",
                self,
                toggled=lambda value: self.canvas.get_graph().set_weighted(value),
            ),
            2,
            0,
        )
        layout.addWidget(QCheckBox("multi", self), 3, 0)

        ### Visual options
        layout.addWidget(QLabel(self, text="Visual"), 0, 1)

        layout.addWidget(QCheckBox("labels", self), 1, 1)

        layout.addWidget(
            QCheckBox(
                "gravity", self, toggled=lambda value: self.canvas.set_forces(value),
            ),
            2,
            1,
        )

        ### Graph actions
        layout.addWidget(QLabel(self, text="Actions"), 0, 2)
        layout.addWidget(QPushButton("complement", self), 1, 2)
        layout.addWidget(QPushButton("reorient", self), 2, 2)

        self.dock_widget.setLayout(layout)

        ### Set the dock menu as the dock widget for the app
        self.dock_menu.setWidget(self.dock_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_menu)

        # WINDOW SETTINGS
        self.show()


app = QApplication(sys.argv)
ex = GraphVisualizer()
sys.exit(app.exec_())
