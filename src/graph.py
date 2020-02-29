"""A class for working with graphs."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, List, Union

from ast import literal_eval


@dataclass(eq=False)
class Node:
    """A class for working with of nodes in a graph."""

    label: str = None
    adjacent: Dict[Node, float] = field(default_factory=dict)

    def get_adjacent(self) -> Dict[Node, float]:
        """Returns the adjacent of the node."""
        return self.adjacent

    def get_label(self) -> str:
        """Returns the label of the node."""
        return self.label

    def set_label(self, label: str):
        """Sets the label of the node to the specified value."""
        self.label = label


@dataclass
class Graph:
    """A class for working with graphs."""

    directed: bool = False
    weighted: bool = False

    nodes: List[Node] = field(default_factory=list)
    components: List[Set[Node]] = field(default_factory=list)

    # a variable used to track, whether we need to recalculate components
    graph_state: int = 0

    def recalculate_weakly_connected(self):
        """Recalculate sets of nodes that are weakly connected.
        TODO: make component calculation faster when only removing a Vertex."""
        self.components = []

        for node in self.nodes:
            # the current set of nodes that we know are reachable from one another
            working_set = set([node] + list(node.adjacent))

            # the index of the set that we added the working set to
            set_index = None

            i = 0
            while i < len(self.components):
                existing_set = self.components[i]

                # if an intersection exists, perform set union
                if len(existing_set.intersection(working_set)) != 0:

                    # if this is the first set to be merged, don't pop it from the list
                    # if we have already merged a set, it means that the working set
                    # joined two already existing sets
                    if set_index is None:
                        existing_set |= working_set
                        set_index = i
                        i += 1
                    else:
                        existing_set |= self.components.pop(set_index)
                        set_index = i - 1
                else:
                    i += 1

            # if we haven't performed any set merges, add the set to the continuity sets
            if set_index is None:
                self.components.append(working_set)

    def weakly_connected(self, n1: Node, n2: Node) -> bool:
        """Returns True if both of the nodes are weakly connected, else False."""
        for component in self.components:
            # if both are in one set, we know for certain that they share a set
            # if only one is, we know that they can't share a set
            # otherwise we don't know and have to check more sets
            if (n1 in component) and (n2 in component):
                return True
            elif n1 in component or n2 in component:
                return False

    def get_directed(self) -> bool:
        """Returns True if the graph is directed, else False."""
        return self.directed

    def set_directed(self, directed: bool):
        """Sets, whether the graph is directed or not."""
        # if we're converting to undirected, make all current vertices go both ways
        if not directed and not self.directed:
            for node in self.nodes:
                for neighbour in node.adjacent:
                    if node is neighbour:
                        # no loops allowed!
                        self.remove_vertex(node, neighbour)
                    else:
                        self.add_vertex(neighbour, node)

        self.directed = directed

    def get_weighted(self) -> bool:
        """Returns True if the graph is weighted and False otherwise."""
        return self.weighted

    def set_weighted(self, value: bool):
        """Sets, whether the graph is weighted or not."""
        self.weighted = value

    def get_weight(self, n1: Node, n2: Node) -> Union[float, None]:
        """Returns the weight of the specified vertex (and None if it doesn't exit or
        the graph is not weighted)."""
        return (
            None
            if not self.is_vertex(n1, n2)
            else self.nodes[self.nodes.index(n1)].adjacent[n2]
        )

    def get_nodes(self) -> List[Node]:
        """Returns a list of nodes of the graph."""
        return self.nodes

    def add_node(self, node: Node):
        """Adds a new node to the graph."""
        self.nodes.append(node)

        self.recalculate_weakly_connected()

    def remove_node(self, n: Node):
        """Removes the node from the graph."""
        self.nodes.remove(n)

        # remove all vertices that point to it
        for node in self.nodes:
            if n in node.adjacent:
                del node.adjacent[n]

        self.recalculate_weakly_connected()

    def add_vertex(self, n1: Node, n2: Node, weight: float = None):
        """Adds a vertex from node n1 to node n2 (and vice versa, if it's not directed).
        Only does so if the given vertex doesn't already exist and can be added (ex.:
        if the graph is not directed and the node wants to point to itself)."""
        if n1 is n2 and not self.directed:
            return

        # from n1 to n2
        n1.adjacent[n2] = weight

        # from n2 to n1
        if not self.directed:
            n2.adjacent[n1] = weight

        self.recalculate_weakly_connected()

    def is_vertex(self, n1: Node, n2: Node) -> bool:
        """Returns True if a vertex exists between the two nodes and False otherwise."""
        return n2 in n1.adjacent

    def toggle_vertex(self, n1: Node, n2: Node):
        """Toggles a connection between to vertexes."""
        if self.is_vertex(n1, n2):
            self.remove_vertex(n1, n2)
        else:
            self.add_vertex(n1, n2)

    def remove_vertex(self, n1: Node, n2: Node):
        """Removes a vertex from node n1 to node n2 (and vice versa, if it's not 
        directed). Only does so if the given vertex exists."""
        # from n1 to n2
        if n2 in n1.adjacent:
            del n1.adjacent[n2]

        # from n2 to n1
        if not self.directed and n1 in n2.adjacent:
            del n2.adjacent[n1]

        self.recalculate_weakly_connected()

    def complement(self):
        """Makes the graph the complement of itself."""
        for n1 in self.nodes:
            for n2 in self.nodes:
                if self.directed or id(n1) < id(n2):
                    self.toggle_vertex(n1, n2)

    @classmethod
    def from_string(cls, string: str) -> Graph:
        """Generates the graph from a given string."""
        graph = None
        node_dictionary = {}

        # add each of the nodes of the given line to the graph
        for line in filter(lambda x: len(x) != 0 or x[0] != "#", string.splitlines()):
            parts = line.strip().split()

            # initialize the graph from the first line, if it hasn't been done yet
            if graph is None:
                directed = parts[1] in ("->", "<-")
                weighted = len(parts) == 3 + directed

                graph = Graph(directed=directed, weighted=weighted)

            # the formats are either 'A B' or 'A <something> B'
            node_names = (parts[0], parts[1 + directed])

            # if weight is present, the formats are:
            # - 'A B num' for undirected graphs
            # - 'A <something> B num' for directed graphs
            weight = 0 if not weighted else literal_eval(parts[2 + directed])

            # create node objects for each of the names (if it hasn't been done yet)
            for name in node_names:
                if name not in node_dictionary:
                    # add it to graph with default values
                    node_dictionary[name] = graph.add_node(Node(label=name))

            # get the node objects from the names
            n1, n2 = node_dictionary[node_names[0]], node_dictionary[node_names[1]]

            # possibly switch places for a reverse arrow
            if parts[1] == "<-":
                n1, n2 = n2, n1

            # add the vertex
            graph.add_vertex(n1, n2, weight)

        return graph

    def to_string(self) -> str:
        """Exports the graph, returning the string."""
        string = ""

        # for each pair n1, n2 where n1_i < n2_i
        for i, n1 in enumerate(self.nodes):
            for n2 in self.nodes[i + 1 :]:
                # TODO: simplify this code
                if self.is_vertex(n1, n2):
                    string += (
                        n1.get_label()
                        + (" -> " if self.directed else " ")
                        + n2.get_label()
                        + (str(self.get_weight(n1, n2)) if self.weighted else "")
                        + "\n"
                    )

                if self.is_vertex(n2, n1) and self.directed:
                    string += (
                        n1.get_label()
                        + (" <- " if self.directed else " ")
                        + n2.get_label()
                        + (str(self.get_weight(n2, n1)) if self.weighted else "")
                        + "\n"
                    )

        return string
