"""This class contains examples of how to use the app to visualize algorithms."""

# TODO: ideas for algorithms
# - BFS, DFS
# - dijkstra
# - graph from score
# - strongly and weakly connected components

from graph import Graph


def bfs(graph: Graph):
    """A BFS implementation."""

    # asserts for the algorithm to function properly
    assert not graph.get_weighted(), "Graph mustn't be weighted."
