# Grafátko [gɾafɑtko]
An app for creating and visualizing graphs and graph-related algorithms.

TODO move updated sample images here

## Installing the app
Simply run `pip install grafatko`.

## Visualizing algorithms
TODO

## Import/export format
The app uses a simple format for importing and exporting graph.
It consists of a list of vertices of the graph.
The syntax is as follows, with the values in square brackets being optional:

`n1 [direction] n2 [weight]`, where
- `n1` and `n2` are labels of the nodes forming the vertex
- `[direction]` is used in directed graphs, and could be either `->` or `<-`
- `[weight]` is the weight of the vertex

Examples of valid graphs can be found in the `examples/` folder.
Note that as long as the file is _not binary_, the extension doesn't matter.
