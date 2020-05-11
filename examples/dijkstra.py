from enum import Enum
from grafatko import *


class State(Enum):
    """A class representing the state of a graph node."""

    unexplored = Color.text()
    open = Color.red()
    closed = Color.background()

    current = Color.blue()


def dijkstra(graph: DrawableGraph):
    """A dijkstra implementation."""
    # get the currently selected nodes
    selected: Set[DrawableNode] = graph.get_selected_nodes()

    assert graph.is_weighted(), "Graph must be weighted."
    assert len(selected) != 0, "Some nodes must be selected."

    graph.set_default_animation_duration(300)

    # set the color and the label of the nodes
    distance: Dict[DrawableNode, float] = {}
    state: Dict[DrawableNode, State] = {}

    for n in graph.get_nodes():
        distance[n] = 0 if n in selected else float("+inf")
        state[n] = State.open if n in selected else State.unexplored

        graph.change_color(n, state[n].value, parallel=True)
        #graph.change_label(n, "0" if n in selected else "∞", parallel=True)

    # while there are nodes that are open
    while any(state[n] is State.open for n in graph.get_nodes()):
        # find the minimum open node
        cur = min(
            graph.get_nodes(),
            key=lambda n: (distance[n]
            + (float("inf") if state[n] is not State.open else 0)),
        )

        graph.change_color(cur, State.current.value)

        # for each adjacent node
        for adj in cur.get_adjacent_nodes():
            # update distances that we can improve
            if distance[adj] > distance[cur] + graph.get_weight(cur, adj):
                distance[adj] = distance[cur] + graph.get_weight(cur, adj)
                state[adj] = State.open

                graph.change_color(adj, State.open.value, parallel=True)
                #graph.change_label(n, graph.get_weight(cur, adj), parallel=True)

        state[cur] = State.closed
        graph.change_color(cur, State.closed.value)
