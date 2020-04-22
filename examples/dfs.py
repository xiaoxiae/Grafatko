from enum import Enum
from grafatko import *


class State(Enum):
    """A class representing the state of a graph node."""

    unexplored = Color.text()
    open = Color.red()
    closed = Color.background()

    current = Color.blue()


def __dfs(node: DrawableNode, graph: DrawableGraph, state):
    """Internal recursive DFS function."""

    # search for unexplored neighbours
    for adjacent in node.get_adjacent_nodes():
        if state[adjacent] is State.unexplored:
            state[adjacent] = State.open
            graph.change_color(adjacent, State.unexplored.value, State.open.value)
            __dfs(adjacent, graph, state)

        # change the color from open to closed
    graph.change_color(node, State.open.value, State.closed.value)
    state[node] = State.closed


def dfs(graph: DrawableGraph):
    """A DFS implementation."""
    # get the currently selected nodes
    selected: Set[DrawableNode] = graph.get_selected_nodes()

    assert not graph.is_weighted(), "Graph mustn't be weighted."
    assert len(selected) != 0, "Some nodes must be selected."

    state: Dict[DrawableNode, State] = {}

    graph.set_default_animation_duration(100)

    # set node states and change colors accordingly
    for n in graph.get_nodes():
        state[n] = State.open if n in selected else State.unexplored
        graph.change_color(n, n.get_color(), state[n].value, parallel=True)

    # run DFS on each of the selected nodes
    for node in selected:
        __dfs(node, graph, state)
