"""This class contains examples of how to use the app to visualize algorithms."""

from enum import Enum
from grafatko import *


class State(Enum):
    """A class representing the state of a BFS node."""

    unexplored = Color.text()
    open = Color.red()
    closed = Color.background()


def bfs(graph: DrawableGraph, canvas):
    """A BFS implementation."""
    # get the currently selected nodes
    selected: List[DrawableNode] = graph.get_selected_nodes()

    assert not graph.is_weighted(), "Graph mustn't be weighted."
    assert len(selected) != 0, "Some nodes must be selected."

    queue = selected  # BFS queue
    state = {n: State.unexplored for n in graph.get_nodes()}

    # mark and color selected
    for n in selected:
        state[n] = State.open
        graph.change_color(n, n.get_color(), State.open.value, parallel=True)

    while len(queue) != 0:
        node = queue.pop(0)

        # search for unexplored neighbours
        for adjacent in node.get_adjacent_nodes():
            if state[adjacent] is State.unexplored:
                # add it to queue and transition color
                queue.append(adjacent)
                state[node] = State.open
                graph.change_color(
                    adjacent, State.unexplored.value, State.open.value, parallel=True
                )

        # change the color from open to closed
        graph.change_color(node, State.open.value, State.closed.value)
        state[node] = State.closed


# TODO: ideas for algorithms
# - BFS, DFS
# - dijkstra
# - graph from score
# - strongly and weakly connected components
