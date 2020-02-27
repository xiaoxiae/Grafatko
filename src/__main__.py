import sys

# GOOD CODE
from typing import *

# GUI
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qtmodern import styles

import webbrowser


# UTILITIES
from functools import partial

from graph import *
from utilities import *


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        painter.drawRect(0, 0, self.width(), self.height())


class GraphVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Widgets
        ## Top menu bar
        self.menubar = self.menuBar()

        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(QAction("Import", self))
        self.file_menu.addAction(QAction("Export", self))
        self.file_menu.addSeparator()
        self.file_menu.addAction(QAction("Exit", self, triggered=exit))

        self.preferences_menu = self.menubar.addMenu("&Preferences")
        self.preferences_menu.addAction(
            QAction(
                "Dark Theme",
                self,
                checkable=True,
                triggered=partial(
                    lambda x, y: styles.dark(x) if y else styles.light(x),
                    QApplication.instance(),
                ),
            )
        )

        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(QAction("Manual", self))
        self.help_menu.addAction(QAction("About", self))
        self.help_menu.addAction(
            QAction(
                "Source Code",
                self,
                triggered=partial(
                    webbrowser.open, "https://github.com/xiaoxiae/GraphVisualizer"
                ),
            )
        )

        ## Canvas (main widget)
        self.canvas = Canvas(parent=self)
        self.canvas.setFixedSize(50, 50)
        self.setCentralWidget(self.canvas)

        # WINDOW SETTINGS
        self.show()


app = QApplication(sys.argv)
ex = GraphVisualizer()
sys.exit(app.exec_())
