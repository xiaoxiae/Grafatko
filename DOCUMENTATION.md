# Documentation
This document serves to shed light onto the inner workings and decisions made in creating this project, resources used, and possible future developments.

---

## Project Structure
It examines each of the `.py` files in the `grafatko` folder, describes their purpose and discusses the classes they contain.
Before going into further detail, here is a brief overview of all of the modules used throughout the project:

- `__init__.py` -- GUI
- `graph.py` -- graph-related things
- `color.py` -- theme-independent colors
- `animation.py` -- graph animations (for algorithms)
- `controls.py` -- keyboard and mouse states
- `utilities.py` -- other utility classes


### `__init__.py`
The file that gets called initially when importing the module.
It contains all of the GUI-related things.

#### `Grafatko(QMainWindow)`
The main window class that builds the UI, creating and setting the positions of the widgets on the screen.

#### `Canvas(QWidget)`
A custom widget class that takes care of drawing the canvas, handling decisions regarding mouse and key presses, and moving nodes around using pre-defined force functions.
This is the main function that handles the user-graph interaction.

### `graph.py`
A module containing everything graph-related.
This includes both the internal graph representation and all functions necessary to draw (and animate) the graph.

#### `Node`
The internal representation of a graph node.
Contains a label and a set of vertex objects that go from the node to some other node.
Although it would likely be much more efficient to store them as a linked list of adjacent nodes, this decision is much better for the object-oriented structure of the project.

#### `Vertex`
The internal representation of a graph vertex.
Essentially a dataclass -- only contains the "from" node, the "to" node and its weight (and some getters and setters).

#### `Graph`
The internal representation of a graph.
Stores nodes/vertices as lists of objects.
Contains both low-level graph-editing functions like adding/removing nodes and vertices, and also functions like reorienting/complementing a graph and checking, if two nodes are weakly connected (necessary for applying forces).

#### `Drawable`
A class representing something that can be drawn, meaning that it has a `draw` function that gets called with a `QPainter`, a `QPalette`, and draws something using it.
Is essentially an interface, since it only contains one abstract method.
Is included for the code to be more readable.

#### `Paintable`
A class for things for which it makes sense to set their color, like a node or a vertex.
Note that a _graph is not one of these_, since it's made up of smaller things that are.
Stores a pen and a brush to draw the said things.
Also has a `get_font_color` method that automatically generates the appropriate font color to be in contrast with the color of the object.

#### `Selectable`
A class for things for which it makes sense to be selected.
It only has getters/setters for checking/setting selected.
Again, _graph is not one of these_, since it's technically selected all the time and it wouldn't make sense for it to inherit this class.

#### `DrawableNode(Drawable, Paintable, Selectable, Node)`
A more specific class for nodes that can be:

- drawn on the canvas
- be animated
- be selected
- have forces act upon them/be dragged

#### `DrawableVertex(Drawable, Paintable, Selectable, Vertex)`
Same as above.
The only difference is that the position is determined by the positions of the nodes that it contains, so it cannot be directly changed (although: TODO? :)).

#### `DrawableGraph(Drawable, Graph)`
Same as above.
It is one of the most important classes, since it is this class that contains all of the API that a user is meant to use to create animations on the graph.
Implements the graph-drawing and animation logic.

### `color.py`
A module for working with colors relative to the current theme of the application, so it's easy to generate a color relative to the current (possibly user-defined) application theme palette, given some color function.

#### `ColorGenerating`
A class that generates a `QColor`, given a color function and a `QPallette`.
An object of this type can be given 

#### `Color(ColorGenerating)`
A class representing a relative color.
It's quite similar to `ColorGenerating`, but has useful class methods for getting commonly used colors.

#### `Colorable`
A class representing something that has a color.

It stores a `ColorGenerating` object that gets called with a `QPalette`.
It is important to understand that this object can be both a `Color` and a `ColorAnimation`, since they both inherit the `ColorGenerating` class and the class that inherits `Colorable` won't know the difference.
This is how the color animations work.

#### `Pen(Colorable)`
A class that returns a `QPen`, when given a `QPalette`. Uses a `ColorGenerating` object to do so.
It's essentially a wrapper to conform to the design pattern that I chose for this part of the application (to be theme-independent, that is).

#### `Brush(Colorable)`
Same as the above, the only difference being that it returns a `QBrush` instead.

### `animation.py`

#### `Animation`
The base animation class that is inherited by all the other animation classes used throughout the project.
Throughout its running time, it returns interpolated values from 0 to 1 (inclusive).
It internally uses a `QElapsedTimer` for tracking the current time and a `QEasingCurve` for interpolating the values.

#### `ColorAnimation(Animation, ColorGenerating)`
An animation that is meant to be used as a drop-in replacement for `Color` objects, but that changes its color function depending on the specified duration and given a specific curve.

### `controls.py`
A module for storing information about the currently pressed keys/buttons/mouse positions/...

#### `Pressable`
A class representing thing that can be pressed (thing for which to makes sense to have an on/off state).

#### `PressableCollection`
A class of collection of `Pressable` objects that provides convenient ways to create, access and update their states.

#### `Keyboard(PressableCollection)`
A keyboard object with common keyboard keys.
It dynamically generates properties from strings so it can be called like `keyboard_obj.space`, which I find quite nice and convenient (although it's Python magic :)).

#### `Mouse(PressableCollection)`
A mouse object that also tracks the current and previous positions of a mouse click.
Dynamically generates properties from strings (just like `Keyboard` does).

### `utilities.py`
A module containing some utility classes, that didn't really fit anywhere else.

#### `Vector`
A class for working with vectors in a convenient way.
It defines operations like addition, subtraction, multiplication, rotation, distance in space...
Is used to store the position of the objects on the screen.
The class is very important to the readability of code, since it makes all vector arithmetics (that is used quite a bit in the project) very pleasant and readable.

#### `Transformation`
A class for representing the current transformation of the canvas widget.
It provides convenience methods for changing the transformation and applying the transformation on points (used in the `Mouse` class to transform the mouse clicks into the coordinates of the canvas).

---

## Things to mention

### Forces
The forces are implemented using a few functions that act on the nodes, depending on how far they are and whether they are connected.
The algorithm examines each unique pair of nodes, calculates the forces and:

- repulses them a little
- attracts them a lot, but only if they share a vertex

To see the actual functions used, see the `repulsion` and `attraction` variables in the `Canvas` class.

### Tree mode
The tree mode exerts additional forces over the nodes, depending on whether some node is currently the root.
It runs BFS from the root node, getting the layers of the graph from root.
After this, it moves forces in each of the layer towards a horizontal line (average of their `y` components) so they are vertically as close as possible.
Also, gravity (a constant vector) is applied so the nodes move "down" (since that's how trees are usually visualized).

---

## Future development
I'm pretty happy with the current state of the project, but there are still some features that I would really like to see added (and bugs to fix) before the `1.0` release.
To see them, visit the [GitHub issues page](https://github.com/xiaoxiae/Grafatko/issues/).

---

## Resources used
There are many things that I had to research before getting this far with the project. 
Here is a list of those that I find were important:

- [PyQt5 documentation](https://doc.qt.io/qtforpython/api.html) for working with the UI library.
- [Průvodce labyrintem algoritmů](http://pruvodce.ucw.cz/) for seeing possible implementations of example algorithms.

---

## Acknowledgements

I would like to thank:

- Veronika Slámová for creating the neat icon for the project.
- Jakub Medek and Michael Bohin for testing and giving feedback.
- Martin Mareš for the great algorithm course that I'm writing this project for.
- Adam Dingle for valuable feedback regarding the project, both providing interesting ideas and discovering new bugs.
- All the users that keep me motivated to continue developing the project.
