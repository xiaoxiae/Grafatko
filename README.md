# Graph Visualizer
The app aims to help creating, visualizing and exporting graphs. It is powered by PyQt5 – a set of Python bindings for the C++ library Qt.

## Running the app
Before running the app, make sure to:
- have [Python](https://www.python.org/) installed.
- install the PyQt5 library by running `pip install pyqt5` in your terminal.

To launch the app, run `__main__.py` using Python.

## Import/export format
The app uses a simple format for importing and exporting graph.
It consists of a list of vertices of the graph.
The syntax is as follows, with the values in square brackets being optional:

`n1 [direction] n2 [w1] [w2]`, where
- `n1` and `n2` are labels of the nodes that are connected
- `[direction]` is only used in directed graphs, and could be either `->` (going from `n1` to `n2`), `<-` (going from `n2` to `n1`) and `<>` (going both ways)
- `[w1]` is the weight of the vertex from `n1` to `n2`
- `[w2]` is the weight of the vertex from `n2` to `n1`; is only used in the case of `n1 <> n2 w1 w2`

Examples of valid graphs can be found in the `graph examples/` folder. 
Note that as long as the file is _not binary_, the extension doesn't matter.

## Sample Images
![Sample Images](https://i.imgur.com/7GU4K6a.png)