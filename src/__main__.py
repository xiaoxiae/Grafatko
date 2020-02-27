import sys

# GOOD CODE
from typing import *

# GUI
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qtmodern import styles  # themes
import webbrowser  # opening the browser


# UTILITIES
from functools import partial

from graph import *
from utilities import *


class Canvas(QWidget):
    # by how much the background is darker and border lighter to standard widget
    lighten_coefficient = 10

    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setBrush(
            QBrush(
                self.palette()
                .color(QPalette.Background)
                .lighter(100 + self.lighten_coefficient),
                Qt.SolidPattern,
            )
        )

        painter.setPen(
            QPen(
                self.palette()
                .color(QPalette.Background)
                .lighter(100 - self.lighten_coefficient),
                Qt.SolidLine,
            )
        )

        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class GraphVisualizer(QMainWindow):
    def __init__(self):
        # TODO: command line argument parsing

        super().__init__()

        # Widgets
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
                    webbrowser.open, "https://github.com/xiaoxiae/GraphVisualizer"
                ),
            )
        )

        ## Canvas (main widget)
        self.canvas = Canvas(parent=self)
        self.canvas.setMinimumSize(100, 200)  # random reasonable minimum size
        self.setCentralWidget(self.canvas)

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
