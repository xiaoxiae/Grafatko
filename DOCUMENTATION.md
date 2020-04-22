# Documentation
This document serves to shed light onto the inner workings and decisions made in creating this project.
It examines each of the `.py` files in the `grafatko` folder, describes their purpose and discusses the classes they contain.

## `__init__.py`
The file that gets called initially when importing the module.
It contains all of the GUI-related things.

### `Grafatko(QMainWindow)`
The main window class that basically just builds the UI, creating and setting the positions of the widgets on the screen.

### `Canvas(QWidget)`
A custom widget class that takes care of drawing the canvas, handling decisions regarding mouse and key presses, and moving nodes around using pre-defined force functions.

## `graph.py`
A module containing everything graph-related.

### `Node`
The internal representation of a graph node.
Contains a label and a set of vertex objects that go from the node to some other node.
Although it would likely be much more efficient to store them as a linked list of adjacent nodes, this decision is much better for the structure of the project.

### `Vertex`
The internal representation of a graph vertex.
Contains the "from" node, the "to" node and its weight.

### `Graph`
The internal representation of a graph.
Contains both low-level graph-editing functions like adding/removing nodes and vertices, and also functions like reorienting/complementing a graph and checking, if two nodes are weakly connected (necessary for applying forces).

### `Drawable`
A class representing something that can be drawn, meaning that it has a `draw` function that gets called with a `QPainter`, a `QPalette`, and draws something using it.

### `Paintable`
A class for things for which it makes sense to set their color, like a node or a vertex.
Note that a _graph is not one of these_, since it's made up of smaller things that are.

### `Selectable`
A class for things for which it makes sense to be selected.
Again, _graph is not one of these_, since it's technically selected all the time and it wouldn't make sense for it to inherit this class.

### `DrawableNode(Drawable, Paintable, Selectable, Node)`
A more specific class for nodes that can be drawn on the canvas, change colors, be selected, have forces act upon them...

### `DrawableVertex(Drawable, Paintable, Selectable, Vertex)`
Same as above.

### `DrawableGraph(Drawable, Graph)`
Same as above.

## `color.py`
A module for working with colors relative to the current theme of the application.

The main purpose of the following color-generating shenanigans is to be able to:

- generate a color relative to the current (possibly user-defined) application theme palette
- replace a color with a color animation and not know the difference

### `ColorGenerating`
A class that generates a `QColor`, given a color function and a `QPallette`.

### `Color(ColorGenerating)`
A class representing a relative color.
It's quite similar to `ColorGenerating`, but has useful class methods for getting commonly used colors.

### `Colorable`
A class representing something that has a color.

### `Pen(Colorable)`
A class that returns a `QPen`, when given a `QPalette`. Uses a `ColorGenerating` object to do so.
It's essentially a wrapper to conform to the design pattern that I chose for this part of the application.

### `Brush(Colorable)`
Same as the above, the only difference being that it returns a `QBrush` instead.

### `ColorAnimation(ColorGenerating)`
A thing that is meant to be used as a `Color`, but that changes its color function depending on the specified duration and given a specific curve.

## `controls.py`
A module for storing information about the currently pressed keys/buttons/mouse positions/...

### `Pressable`
A class representing thing that can be pressed (thing for which to makes sense to have an on/off state).

### `PressableCollection`
A class of collection of `Pressable` objects that provides convenient ways to access and update their states.

### `Keyboard(PressableCollection)`
A keyboard object with common keyboard keys.

### `Mouse(PressableCollection)`
A mouse object that also tracks the current and previous positions of a mouse click.

## `utilities.py`
A module containing some utility classes, that didn't really fit anywhere else.

### `Vector`
A class for working with vectors in a convenient way.
It defines operations like addition, subtraction, multiplication, rotation, distance in space...
Is used to store the position of the objects on the screen.

### `Transformation`
A class for representing the current transformation of the canvas widget.
It stores a `scale: int` and a `translation: Vector` variables to do so and provides convenience methods for both changing the transformation and applying the transformation on points.
Is used, for example, in the `Mouse` class to transform the mouse clicks into the coordinates of the canvas.
