import sys

# CLEAN CODE
from typing import *

# GUI
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qtmodern import styles  # themes
import webbrowser  # opening the browser


# UTILITIES
from functools import partial
from random import random
from math import radians

from graph import *
from utilities import *


class Canvas(QWidget):
    # WIDGET OPTIONS
    lighten_coefficient = 10  # how much lighter/darker the canvas is (to background)

    scale_coefficient: float = 8  # by how much the scale changes on scroll

    def __init__(self, parent=None):
        super().__init__(parent)

        # the graph the canvas is displaying
        self.graph = Graph()

        # positioning
        self.scale: float = 1
        self.translation: float = Vector(0, 0)

        # timer that runs the simulation (60 times a second... once every ~= 17ms)
        QTimer(self, interval=17, timeout=self.update).start()

    def update(self, *args):
        """A function that gets periodically called to update the canvas."""
        # the forces that act on the nodes
        repulsion = lambda distance: 1 / distance * 10
        attraction = lambda distance: -(distance - 80) / 10

        for i, n1 in enumerate(self.graph.get_nodes()):
            for n2 in self.graph.get_nodes()[i + 1 :]:
                # if they are not at least weakly connected, no forces act on them
                if not self.graph.weakly_connected(n1, n2):
                    continue

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

        self.paint_background(painter)

        # translate the world
        painter.translate(*self.translation)
        painter.scale(self.scale, self.scale)

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

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; node rotation and zoom."""
        # positive/negative for scrolling away from/towards the user
        scroll_distance = radians(event.angleDelta().y() / self.scale_coefficient)

        mouse_coordinates = Vector(event.pos().x(), event.pos().y())

        prev_scale = self.scale
        self.scale *= 2 ** (scroll_distance)

        # adjust translation so the x and y of the mouse stay in the same spot
        self.translation -= mouse_coordinates * (self.scale - prev_scale)


class GraphVisualizer(QMainWindow):
    def __init__(self):
        # TODO: command line argument parsing
        # -- dark and stuff

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
        layout.addWidget(QCheckBox("directed", self), 1, 0)
        layout.addWidget(QCheckBox("weighted", self), 2, 0)
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
