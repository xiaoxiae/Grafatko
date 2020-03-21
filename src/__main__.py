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
    """A small class for storing information about the mouse position on canvas."""

    position: Vector = None  # its position on the app window
    pressed: Vector = None  # whether it is currently being pressed


class Canvas(QWidget):
    # WIDGET OPTIONS
    lighten_coefficient = 10  # how much lighter/darker the canvas is (to background)

    # positioning
    scale_coefficient: float = 8  # by how much the scale changes on scroll

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
        # the forces that act on the nodes
        repulsion = lambda distance: (1 / distance) ** 2
        attraction = lambda distance: -(distance - 8) / 10

        for i, n1 in enumerate(self.graph.get_nodes()):
            for n2 in self.graph.get_nodes()[i + 1 :]:
                # TODO: add weakly_connected check
                # if they are not at least weakly connected, no forces act on them
                # if not self.graph.weakly_connected(n1, n2):
                #    continue

                d = n1.get_position().distance(n2.get_position())

                # if they are on top of each other, nudge one of them slightly
                if d == 0:
                    n1.add_force(Vector(random(), random()))
                    continue

                # unit vector from n1 to n2
                uv = (n2.get_position() - n1.get_position()).unit()

                # the size of the repel force between the two nodes
                fr = repulsion(d)

                # add a repel force to each of the nodes, in the opposite directions
                n1.add_force(-uv * fr)
                n2.add_force(uv * fr)

                # if they are also connected, add the attraction force
                # the direction does not matter -- it would look weird for directed
                if self.graph.is_vertex(n1, n2) or self.graph.is_vertex(n2, n1):
                    fa = attraction(d)

                    n1.add_force(-uv * fa)
                    n2.add_force(uv * fa)

            n1.evaluate_forces()

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
        self.graph.draw(painter)

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

    def mouse_position(self, clamp=True) -> Union[Vector, None]:
        """Returns the mouse coordinates adjusted for translation and scale of the
        canvas. If they are outside of the canvas then they are scaled down."""
        if self.mouse.position is None:
            return None

        x, y = self.mouse.position

        # possibly clamp the values and don't return None
        if clamp:
            # a clamp function
            f = lambda v, min, max: min if v < min else max if v > max else v
            x = f(x, 0, self.width())
            y = f(y, 0, self.height())

        # else check for None
        elif not (0 <= x <= self.width()) or not (0 <= y <= self.height()):
            return None

        # return the mouse coordinates, accounting for canvas translation and scale
        return (Vector(x, y) - self.translation) / self.scale

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window."""
        self.mouse.position = Vector(event.pos().x(), event.pos().y())

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released."""
        self.mouse.pressed = False
        self.mouse.position = Vector(event.pos().x(), event.pos().y())

    def mousePressEvent(self, event):
        """Is called when a mouse button is released."""
        self.mouse.pressed = True
        self.mouse.position = Vector(event.pos().x(), event.pos().y())

        shift_pressed = QApplication.keyboardModifiers() == Qt.ShiftModifier

        if event.button() == Qt.LeftButton:
            # either select the node, or add it to selected when shift is pressed
            if (node := self.graph.node_at_position(self.mouse_position())) != None:
                if not shift_pressed or self.selected_nodes == None:
                    self.selected_nodes = []

                self.selected_nodes.append(node)

            # else deselect them all
            else:
                self.selected_nodes = None

        elif event.button() == Qt.RightButton:
            # if there isn't a node at the position, add it
            if (node := self.graph.node_at_position(self.mouse_position())) is None:
                node = DrawableNode(self.mouse_position())

                self.graph.add_node(node)

            # if there is a node and if some nodes are selected, connect them to it
            if self.selected_nodes is not None:
                for selected_node in self.selected_nodes:
                    self.graph.add_vertex(selected_node, node)

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; node rotation and zoom."""
        # positive/negative for scrolling away from/towards the user
        scroll_distance = radians(event.angleDelta().y() / self.scale_coefficient)

        # NOTE: it is _super important_ that mouse_position() gets called before
        # scale is adjusted, since the scale changes what mouse_position() returns...
        position = self.mouse_position()

        # adjust the scale
        previous_scale = self.scale
        self.scale *= 2 ** scroll_distance

        # adjust translation so the x and y of the mouse stay in the same spot
        self.translation -= position * (self.scale - previous_scale)

    def get_graph(self):
        """Get the current graph."""
        return self.graph


class GraphVisualizer(QMainWindow):
    def __init__(self):
        # TODO: command line argument parsing (--dark and stuff)
        # TODO: hide toolbar with f-something

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
        layout.addWidget(QCheckBox("gravity", self), 2, 1)

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
