import os
import sys
import webbrowser
import argparse
from importlib.machinery import SourceFileLoader
from functools import partial
from random import random
from math import pi

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from qtmodern import styles

from grafatko.controls import *
from grafatko.graph import *


class Canvas(QWidget):
    # WIDGET OPTIONS
    contrast_coefficient = 10
    background_brush = Brush(Color.background().lighter(100 + contrast_coefficient))
    background_pen = Pen(Color.background().darker(100 + contrast_coefficient))

    # whether the forces are enabled/disabled
    forces: bool = True

    # _ because the lambda gets self as the first argument
    repulsion = lambda _, distance: (1 / distance) ** 2
    attraction = lambda _, distance: -(distance - 6) / 3
    tree = lambda _, v: v * 0.3
    gravity = lambda _: Vector(0, 0.1)

    # the radius around which to check if the node moved when shift-selecting nodes
    mouse_toggle_radius = 0.1

    def __init__(self, line_edit, parent, update_ui_callback):
        super().__init__(parent)
        # GRAPH
        self.graph = DrawableGraph(
            selected_changed=self.selected_changed, animation_stopped=update_ui_callback
        )

        # CANVAS STUFF
        self.transformation = Transformation(self)

        # MOUSE
        self.mouse = Mouse(self.transformation)
        self.setMouseTracking(True)

        self.keyboard = Keyboard()

        self.line_edit = line_edit
        self.line_edit.textEdited.connect(self.line_edit_changed)

        # timer that runs the simulation (60 times a second... once every ~= 17ms)
        QTimer(self, interval=17, timeout=self.update).start()

        self.update_ui_callback = update_ui_callback

    def update(self, *args):
        """A function that gets periodically called to update the canvas."""
        # if the graph is rooted and we want to do forces
        root = self.graph.get_root()
        if root is not None and self.forces:
            distances = self.graph.get_distance_from_root()

            # calculate the forces within each BFS layer from root
            for layer in distances:
                if len(distances[layer]) < 1:
                    continue

                pivot = Vector.average([n.get_position() for n in distances[layer]])

                for node in distances[layer]:
                    vector = Vector(0, pivot[1] - node.get_position()[1])
                    node.add_force(self.tree(vector))

            # add gravity
            for node in self.graph.get_nodes():
                if node is not root and self.graph.weakly_connected(node, root):
                    node.add_force(self.gravity())

        # only move the nodes when forces are enabled
        if self.forces:
            for i, n1 in enumerate(self.graph.get_nodes()):
                for n2 in self.graph.get_nodes()[i + 1 :]:
                    # only apply force, if n1 and n2 are weakly connected
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
                    fr = self.repulsion(d)

                    # add a repel force to each of the nodes, in the opposite directions
                    n1.add_force(-uv * fr)
                    n2.add_force(uv * fr)

                    # if they are also connected, add the attraction force
                    # the direction does not matter -- it would look weird for directed
                    if n1.is_adjacent_to(n2) or n2.is_adjacent_to(n1):
                        fa = self.attraction(d)

                        n1.add_force(-uv * fa)
                        n2.add_force(uv * fa)

                # root is special
                if n1 is root:
                    n1.clear_forces()
                else:
                    n1.evaluate_forces()

        # if space is being pressed, center around the currently selected nodes
        # if there are none, center around their average
        if self.keyboard.space.pressed():
            sn = self.graph.get_selected_nodes()
            pivot = None

            if len(sn) != 0:
                pivot = Vector.average([n.get_position() for n in sn])
            elif len(self.graph.get_nodes()) != 0:
                pivot = Vector.average(
                    [n.get_position() for n in self.graph.get_nodes()]
                )

            if pivot is not None:
                self.transformation.center(pivot)

        super().update(*args)

    def line_edit_changed(self, text):
        """Called when the line edit associated with the Canvas changed."""
        selected = self.graph.get_selected_objects()

        if type(selected[0]) is DrawableNode:
            selected[0].set_label(text)
        else:
            try:
                weight = int(text)
            except:
                try:
                    weight = float(text)
                except:
                    weight = None

            if weight is not None:
                for v in selected:
                    self.graph.set_weight(v, weight)

    def selected_changed(self):
        """Called when something in the graph gets selected/deselected."""
        selected = self.graph.get_selected_objects()

        # if nothing is selected, let the user know
        if len(selected) == 0:
            self.line_edit.setReadOnly(True)
            self.line_edit.setText("Select a node or a vertex to edit.")

        # else if more than two things are selected
        elif len(selected) >= 2 and not (
            type(selected[0]) is DrawableVertex
            and type(selected[1]) is DrawableVertex
            and selected[0][0] == selected[1][1]
            and selected[0][1] == selected[1][0]
        ):
            self.line_edit.setReadOnly(True)
            self.line_edit.setText("Select only one node or a vertex to edit.")

        # else if one is, focus on it
        else:
            self.line_edit.setReadOnly(False)

            if type(selected[0]) is DrawableNode:
                self.line_edit.setText(selected[0].get_label() or "")
            else:
                self.line_edit.setText(str(selected[0].get_weight()))

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        palette = self.palette()

        # clip
        painter.setClipRect(0, 0, self.width(), self.height())

        # draw the background
        painter.setBrush(self.background_brush(palette))
        painter.setPen(self.background_pen(palette))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        # transform the coordinates according to the current state of the canvas
        self.transformation.transform_painter(painter)

        # draw the graph
        self.graph.draw(painter, palette)

    def keyReleaseEvent(self, event):
        """Called when a key press is registered."""
        key = self.keyboard.released_event(event)

        # if we release shift, stop shift-dragging the nodes
        if key is self.keyboard.shift:
            self.stop_shift_dragging_nodes()

    def start_shift_dragging_nodes(self, additional: List[DrawableNode] = []):
        """Start dragging nodes that are weakly connected to some selected nodes (and
        possibly also to those provided)."""
        selected = self.graph.get_selected_nodes() + additional

        for n in self.graph.get_weakly_connected(*selected):
            if not n.is_dragged():
                n.start_drag(self.mouse.get_position())

    def stop_shift_dragging_nodes(self):
        """Stop dragging nodes that are weakly connected to some selected nodes."""
        selected = self.graph.get_selected_nodes()

        for n in self.graph.get_weakly_connected(*selected):
            if n.is_dragged() and n not in selected:
                n.stop_drag()

    def keyPressEvent(self, event):
        """Called when a key press is registered."""
        key = self.keyboard.pressed_event(event)

        # toggle graph root on r press
        if key is self.keyboard.r:
            selected = self.graph.get_selected_nodes()

            if self.graph.get_root() is not None:
                self.graph.set_root(None)

            elif len(selected) == 1:
                self.graph.set_root(selected[0])

        if key is self.keyboard.delete:
            for node in self.graph.get_selected_nodes():
                self.graph.remove_node(node)

            for vertex in self.graph.get_selected_vertices():
                self.graph.remove_vertex(vertex[0], vertex[1])

        elif key is self.keyboard.shift and self.mouse.left.pressed():
            self.start_shift_dragging_nodes()

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the canvas."""
        self.mouse.moved_event(event)

        pressed_node = self.graph.node_at_position(self.mouse.get_position())

        if (
            self.mouse.left.pressed()
            and pressed_node is not None
            and self.mouse.current_last_distance() > self.mouse_toggle_radius
            and len(self.graph.get_dragged_nodes()) > 0
        ):
            self.select(pressed_node)

        # move dragged nodes (unless we are holding down space, centering on them)
        # also move the canvas (unless holding down space)
        if not self.keyboard.space.pressed():
            for node in self.graph.get_nodes():
                if node.is_dragged():
                    node.set_position(self.mouse.get_position())

            if self.mouse.middle.pressed():
                # move canvas when the middle button is pressed
                curr = self.mouse.get_position()
                prev = self.mouse.get_previous_position()
                self.transformation.translate(curr - prev)

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released."""
        self.setFocus()  # done so that key strokes register
        key = self.mouse.released_event(event)

        # get the node and the vertex at the position where we clicked
        pressed_node = self.graph.node_at_position(self.mouse.get_position())
        pressed_vertices = self.graph.vertices_at_position(self.mouse.get_position())

        # stop dragging the nodes if left is released
        if key is self.mouse.left:
            for node in self.graph.get_nodes():
                node.stop_drag()

            # toggle if we haven't moved a lot
            if self.mouse.current_last_distance() <= self.mouse_toggle_radius and self.keyboard.shift.pressed():
                if pressed_node is not None:
                    self.graph.toggle(pressed_node)

                for vertex in pressed_vertices:
                    self.graph.toggle(vertex)

    def mousePressEvent(self, event):
        """Called when a left click is registered."""
        self.setFocus()  # done so that key strokes register
        key = self.mouse.pressed_event(event)

        # get the node and the vertex at the position where we clicked
        pressed_node = self.graph.node_at_position(self.mouse.get_position())
        pressed_vertices = self.graph.vertices_at_position(self.mouse.get_position())

        if key is self.mouse.left:
            # if shift is not pressed, select the pressed thing immediately and deselect
            # everything else
            if not self.keyboard.shift.pressed():
                self.graph.deselect_all()

                # also start the drag if it's a node
                if pressed_node is not None:
                    self.select(pressed_node)
                    pressed_node.start_drag(self.mouse.get_position())

                for vertex in pressed_vertices:
                    self.select(vertex)

            # else just start regular drag on the pressed node
            else:
                if pressed_node is not None:
                    pressed_node.start_drag(self.mouse.get_position())
                    self.start_shift_dragging_nodes([pressed_node])

        if key is self.mouse.right:
            selected = self.graph.get_selected_nodes()

            if pressed_node is None:
                # if there isn't a node at the position, create a new one, connect
                # all selected to it and select
                pressed_node = DrawableNode(position=self.mouse.get_position())
                self.graph.add_node(pressed_node)

                for node in selected:
                    self.graph.add_vertex(node, pressed_node)

                self.select(pressed_node)
            else:
                # if there is, toggle vertices from selected to it
                for node in selected:
                    self.graph.toggle_vertex(node, pressed_node)

    def wheelEvent(self, event):
        """Is called when the mouse wheel is turned."""
        delta = radians(event.angleDelta().y() / 8)

        # rotate nodes on shift press
        if self.keyboard.shift.pressed():
            selected = self.graph.get_selected_nodes()
            if len(selected) != 0:
                nodes = self.graph.get_weakly_connected(
                    *self.graph.get_selected_nodes()
                )
                pivot = Vector.average([n.get_position() for n in selected])
                self.rotate_about(nodes, delta, pivot)

        # zoom on canvas on not shift press
        else:
            # if some nodes are being centered on, don't use mouse
            nodes = self.graph.get_selected_nodes()
            if self.keyboard.space.pressed() and len(nodes) != 0:
                positions = [p.get_position() for p in nodes]
                self.transformation.zoom(Vector.average(positions), delta)
            else:
                self.transformation.zoom(self.mouse.get_position(), delta)

    def rotate_about(self, nodes: Sequence[DrawableNode], angle: float, pivot: Vector):
        """Rotate about the average of selected nodes by the angle."""
        for node in nodes:
            node.set_position(node.get_position().rotated(angle, pivot), True)

    def select(self, obj: Union[DrawableNode, DrawableVertex]):
        """Select the given node/vertex."""
        # only select one when shift is not pressed
        if not self.keyboard.shift.pressed():
            self.graph.deselect_all()

        # else just select it
        self.graph.select(obj)

    def get_graph(self):
        """Get the current graph."""
        return self.graph

    def set_forces(self, value: bool):
        """Enable/disable the forces that act on the nodes."""
        self.forces = value

    def import_graph(self):
        """Prompt a graph (from file) import."""
        path = QFileDialog.getOpenFileName()[0]

        if path == "":
            return

        try:
            # create the graph
            new_graph = DrawableGraph.from_string(
                open(path, "r").read(),
                selected_changed=self.selected_changed,
                animation_stopped=self.update_ui_callback,
            )

            if new_graph is not None:
                self.graph = new_graph

                # make the graph less jittery by setting the positions to a circle
                for i, node in enumerate(self.graph.get_nodes()):
                    node.set_position(
                        Vector(3, 3).rotated(i * (2 * pi / len(self.graph.get_nodes())))
                    )

            # center on it (immediately)
            self.transformation.center(
                Vector.average([n.get_position() for n in self.graph.get_nodes()]),
                center_smoothness=1,
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error!", "An error occurred when importing the graph."
            )

        self.update_ui_callback()

    def export_graph(self):
        """Prompt a graph (from file) export."""
        path = QFileDialog.getSaveFileName()[0]

        if path == "":
            return

        try:
            with open(path, "w") as f:
                f.write(self.graph.to_string())
        except Exception as e:
            QMessageBox.critical(
                self, "Error!", "An error occurred when exporting the graph."
            )

            # clean-up
            os.remove(path)

    def run_algorithm(self):
        """Select a file containing an algorithm and run it."""
        path = QFileDialog.getOpenFileName()[0]

        if path == "":
            return

        if not path.endswith(".py"):
            QMessageBox.critical(self, "Error!", "The file must be a Python program.")
            return

        try:
            filename = os.path.basename(path)[:-3]
            cls = SourceFileLoader(filename, path).load_module()
            getattr(cls, filename)(self.graph)
        except AssertionError as e:
            QMessageBox.critical(self, "Error!", str(e))
        except AttributeError as e:
            QMessageBox.critical(self, "Error!", f"Function '{filename}' not found.")
        except Exception as e:
            QMessageBox.critical(
                self, "Error!", f"An error occurred when running the algorithm.\n\n{e}",
            )

        self.update_ui_callback()


class Grafatko(QMainWindow):
    def __init__(self, arguments):
        super().__init__()

        styles.light(QApplication.instance())

        # Widgets
        ## Canvas (main widget)
        self.line_edit = QLineEdit(self)

        self.canvas = Canvas(self.line_edit, self, self.update_ui)
        self.canvas.setMinimumSize(100, 200)  # reasonable minimum size
        self.setCentralWidget(self.canvas)

        ## Top menu bar
        self.menubar = self.menuBar()

        # menu bar separator
        self.sep = QAction()
        self.sep.setSeparator(True)

        # file menu
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addActions(
            [
                QAction("&Import", self, triggered=lambda: self.canvas.import_graph()),
                QAction("&Export", self, triggered=lambda: self.canvas.export_graph()),
                self.sep,
                QAction("&Quit", self, triggered=exit),
            ]
        )

        # set to light by default (unless there is an argument to set it to dark)
        if arguments.dark:
            styles.dark(QApplication.instance())
        else:
            styles.light(QApplication.instance())

        # preference menu
        self.preferences_menu = self.menubar.addMenu("&Preferences")
        self.preferences_menu.addAction(
            QAction(
                "&Dark Theme",
                self,
                checkable=True,
                checked=arguments.dark,
                triggered=partial(
                    lambda x, y: styles.dark(x) if y else styles.light(x),
                    QApplication.instance(),
                ),
            )
        )

        # algorithm menu
        self.help_menu = self.menubar.addMenu("&Algorithms")
        self.help_menu.addAction(
            QAction("&Run", self, triggered=self.canvas.run_algorithm)
        )

        ## Dock
        # TODO: shrink after leaving the dock
        # TODO: disable vertical resizing
        self.dock_menu = QDockWidget("Settings", self)
        self.dock_menu.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.dock_menu.setFeatures(QDockWidget.DockWidgetFloatable)

        layout = QGridLayout()

        ## Widgets
        self.directed_checkbox = QCheckBox("directed", self, toggled=self.set_directed)

        self.weighted_checkbox = QCheckBox(
            "weighted",
            self,
            toggled=lambda value: self.canvas.get_graph().set_weighted(value),
        )

        self.reorient_pushbutton = QPushButton(
            "reorient", self, pressed=lambda: self.canvas.get_graph().reorient()
        )

        self.pause_pushbutton = QPushButton(
            "pause", self, pressed=lambda: self.canvas.get_graph().pause_animations(),
        )

        self.resume_pushbutton = QPushButton(
            "resume", self, pressed=lambda: self.canvas.get_graph().resume_animations(),
        )

        self.clear_pushbutton = QPushButton(
            "clear", self, pressed=self.clear_animations,
        )

        self.labels_checkbox = QCheckBox(
            "labels",
            self,
            toggled=lambda value: self.canvas.get_graph().set_show_labels(value),
            checked=True,
        )

        self.gravity_checkbox = QCheckBox(
            "gravity",
            self,
            toggled=lambda value: self.canvas.set_forces(value),
            checked=True,
        )

        self.complement_pushbutton = QPushButton(
            "complement", self, pressed=lambda: self.canvas.get_graph().complement()
        )

        widgets = {
            (0, 0): QLabel(self, text="Graph"),
            (1, 0): self.directed_checkbox,
            (2, 0): self.weighted_checkbox,
            (0, 1): QLabel(self, text="Visual"),
            (1, 1): self.labels_checkbox,
            (2, 1): self.gravity_checkbox,
            (0, 2): QLabel(self, text="Actions"),
            (1, 2): self.complement_pushbutton,
            (2, 2): self.reorient_pushbutton,
            (0, 3, 1, 2): QLabel(self, text="Animations"),
            (1, 3, 1, 1): self.pause_pushbutton,
            (1, 4, 1, 1): self.resume_pushbutton,
            (2, 3, 1, 2): self.clear_pushbutton,
            (3, 0, 1, -1): self.line_edit,
        }

        # help menu
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addActions(
            [
                QAction(
                    "&About",
                    self,
                    triggered=lambda: QMessageBox.information(
                        self,
                        "About",
                        "This application was created as a semester project for a "
                        "programming class at <a href='https://www.mff.cuni.cz/en'>MFF UK</a> "
                        "by Tomáš Sláma. It's open source (see the tab below) and licensed "
                        "under MIT, so do as you please with the code and anything else "
                        "related to the project.",
                    ),
                ),
                QAction(
                    "&Source Code",
                    self,
                    triggered=partial(
                        # TODO: make non-blocking
                        webbrowser.open,
                        "https://github.com/xiaoxiae/Grafatko",
                    ),
                ),
            ]
        )

        for k, v in widgets.items():
            layout.addWidget(v, *k)

        self.dock_widget = QWidget()
        self.dock_widget.setLayout(layout)

        ### Set the dock menu as the dock widget for the app
        self.dock_menu.setWidget(self.dock_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_menu)

        # set the UI buttons accordingly
        self.update_ui()

        # WINDOW SETTINGS
        self.setWindowIcon(QIcon("icon.ico"))
        self.setWindowTitle("Grafátko")
        self.show()

    def keyPressEvent(self, event):
        self.canvas.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.canvas.keyReleaseEvent(event)

    def clear_animations(self):
        """Clear animations and update the UI (to disable the animation buttons)."""
        self.canvas.get_graph().clear_animations()
        self.update_ui()

    def set_directed(self, value):
        """Set the direction of the graph, updating the UI."""
        self.canvas.get_graph().set_directed(value)
        self.update_ui()

    def update_ui(self):
        """Update the UI according to the state of the canvas. Is triggered when canvas
        lets this class know that something has changed."""
        animations_active = self.canvas.get_graph().animations_active()

        self.clear_pushbutton.setEnabled(animations_active)
        self.pause_pushbutton.setEnabled(animations_active)
        self.resume_pushbutton.setEnabled(animations_active)

        self.weighted_checkbox.setChecked(self.canvas.get_graph().is_weighted())
        self.directed_checkbox.setChecked(self.canvas.get_graph().is_directed())

        self.reorient_pushbutton.setEnabled(self.canvas.get_graph().is_directed())

        # to prevent weird focus on textbox
        self.setFocus()


def run():
    """An entry point to the GUI."""

    parser = argparse.ArgumentParser(
        description="An app for creating and visualizing graphs and graph-related algorithms.",
    )

    parser.add_argument(
        "-d",
        "--dark",
        dest="dark",
        action="store_true",
        help="start the app in dark mode",
    )

    app = QApplication(sys.argv)
    ex = Grafatko(parser.parse_args())
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
