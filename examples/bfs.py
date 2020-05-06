from enum import Enum
from grafatko import *


class State(Enum):
    """A class representing the state of a node."""

    unexplored = Color.text()
    open = Color.red()
    closed = Color.background()

    current = Color.blue()


def bfs(graph: DrawableGraph):
    """A BFS implementation."""
    # get the currently selected nodes
    selected: Set[DrawableNode] = graph.get_selected_nodes()

    assert not graph.is_weighted(), "Graph mustn't be weighted."
    assert len(selected) != 0, "Some nodes must be selected."

    queue = selected  # BFS queue
    state: Dict[DrawableNode, State] = {}

    graph.set_default_animation_duration(100)

    # set node states and change colors accordingly
    for n in graph.get_nodes():
        state[n] = State.open if n in selected else State.unexplored
        graph.change_color(n, state[n].value, parallel=True)

    while len(queue) != 0:
        node = queue.pop(0)
        graph.change_color(node, State.current.value)

        # search for unexplored neighbours
        for adjacent in node.get_adjacent_nodes():
            if state[adjacent] is State.unexplored:
                queue.append(adjacent)
                state[adjacent] = State.open
                graph.change_color(adjacent, State.open.value, parallel=True)

        # change the color from open to closed
        graph.change_color(node, State.closed.value)
        state[node] = State.closed
