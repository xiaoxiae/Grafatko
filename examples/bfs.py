"""This class contains examples of how to use the app to visualize algorithms."""

from enum import Enum
from grafatko import DrawableGraph, DrawableNode, Color


class State(Enum):
    """A class representing the state of a BFS node."""

    Unexplored = Color.DEFAULT
    Open = Color.GREEN
    Closed = Color.BLUE


def bfs(graph: DrawableGraph):
    """A function that runs BFS on the given graph."""
    # get the currently selected nodes
    selected = graph.get_selected()

    # assertions for the algorithm to work properly
    assert not graph.get_weighted(), "Graph mustn't be weighted."
    assert len(selected) == 0, "Some nodes must be selected."

    # the algorithm itself
    queue = selected
    state: Dict[DrawableNode, State] = {n: State.Open for n in selected}

    while len(queue) != 0:
        node = queue.pop(0)

        for adjacent in node.get_adjacent():
            if state[adjacent] is State.Unexplored:
                queue.append(adjacent)
                state[node] = State.Open

        state[node] = State.Closed


# TODO: ideas for algorithms
# - BFS, DFS
# - dijkstra
# - graph from score
# - strongly and weakly connected components
