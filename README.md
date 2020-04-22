# Grafátko [gɾafɑtko]
An app for creating and visualizing graphs and graph-related algorithms.

![examples](example.png?raw=true "An example of the GUI")

## Running Grafátko
First, install the app by running `pip install grafatko`.
Then you can simply run the `grafatko` command from a terminal of your choice.

## Controls

### Mouse
- **right button** creates new nodes/vertices
- **left button** selects and drags nodes/vertices around the screen
- **middle button** pans the canvas
- **mouse wheel** zooms/rotates nodes about, depending on whether shift is pressed

### Keyboard
- **r** toggles 'tree mode' for smoother visualisation of trees
	- essentially applies special forces on the nodes to group them by distance from the currently selected node
	- only works if a single mode is selected
- **space** centers on the currently selected nodes
- **delete** deletes the currently selected items

## Visualizing algorithms
The app allows for visualising custom algorithms on the currently edited graph.
Examples of valid programs can be found in the `examples/` folder.

After creating a graph, you can go to `Algorithms -> Run` and select the one you want to run on the graph.
The program then calls a function with the same name as the file, the only parameter being the `DrawableGraph` object to run the algorithm on.

## Importing/exporting graphs
The app uses a simple format for importing and exporting graph.
It consists of a list of vertices of the graph, with possible specifications to the direction and the weight of the given vertex.

A single line has the format `n1 [direction] n2 [weight]`, where:
- `n1` and `n2` are labels of the nodes forming the vertex, containing no whitespace characters
- `[direction]` is used in directed graphs, and could be either `->` or `<-`
- `[weight]` is used in weighted graphs, denotes the weight of the vertex

Examples of valid graphs can be found in the `examples/` folder.
