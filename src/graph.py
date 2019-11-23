from __future__ import annotations
from dataclasses import dataclass
from typing import Set, List, Union


class Node:
    """A class for working with of nodes in a graph."""

    def __init__(self, position: Vector, radius: float, label: str = None):
        self.position = position
        self.radius = radius
        self.label = label

        self.neighbours: Dict[Node, float] = {}
        self.forces: List[Vector] = []

    def get_x(self) -> float:
        """Returns the x coordinate of the node."""
        return self.position[0]

    def get_y(self) -> float:
        """Returns the y coordinate of the node."""
        return self.position[1]

    def get_position(self) -> Vector:
        """Returns the y coordinate of the node."""
        return self.position

    def get_radius(self) -> float:
        """Returns the radius of the node."""
        return self.radius

    def get_neighbours(self) -> Dict[Node, float]:
        """Returns the neighbours of the node."""
        return self.neighbours

    def get_label(self) -> str:
        """Returns the label of the node."""
        return self.label

    def set_x(self, value: float):
        """Sets the x coordinate of the node to the specified value."""
        self.position[0] = value

    def set_y(self, value):
        """Sets the y coordinate of the node to the specified value."""
        self.position[1] = value

    def set_position(self, value: Vector):
        """Sets the position of the node to the specified value."""
        self.position = value

    def set_label(self, label: str):
        """Sets the label of the node to the specified value."""
        self.label = label

    def add_force(self, force: Vector):
        """Adds a force that is acting upon the node to the force list."""
        self.forces.append(force)

    def evaluate_forces(self):
        """Evaluates all of the forces acting upon the node and moves it accordingly."""
        while len(self.forces) != 0:
            self.position += self.forces.pop()


class Graph:
    """A class for working with graphs."""

    def __init__(self, directed=False, weighted=False):
        self.directed = directed
        self.weighted = weighted

        self.nodes: List[Node] = []
        self.components: Set[Node] = []

    def calculate_components(self):
        """Calculate the components of the graph.
        MAJOR TODO: make component calculation faster when only removing a Vertex."""
        self.components = []

        for node in self.nodes:
            # the current set of nodes that we know are reachable from one another
            working_set = set([node] + list(node.get_neighbours()))

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

    def share_component(self, n1: Node, n2: Node) -> bool:
        """Returns True if both of the nodes are in the same component, else False."""
        for component in self.components:
            n1_in_s, n2_in_s = n1 in component, n2 in component

            # if both are in one set, we know for certain that they share a set
            # if only one is in a set, we know for certain that they can't share a set
            # otherwise, we can't be sure and have to check additional sets
            if n1_in_s and n2_in_s:
                return True
            elif n1_in_s or n2_in_s:
                return False

    def is_directed(self) -> bool:
        """Returns True if the graph is directed, else False."""
        return self.directed

    def set_directed(self, value: bool):
        """Sets, whether the graph is directed or not."""
        if not value:
            # make all vertexes go both ways
            for node in self.get_nodes():
                for neighbour in node.get_neighbours():
                    self.add_vertex(neighbour, node, weight=0)

        self.directed = value

    def is_weighted(self) -> bool:
        """Returns True if the graph is weighted and False otherwise."""
        return self.weighted

    def set_weighted(self, value: bool):
        """Sets, whether the graph is weighted or not."""
        self.weighted = value

    def get_weight(self, n1: Node, n2: Node) -> Union[float, None]:
        """Returns the weight of the specified vertex and None if it doesn't exist."""
        return (
            None
            if not self.does_vertex_exist(n1, n2)
            else self.nodes[self.nodes.index(n1)].neighbours[n2]
        )

    def get_nodes(self) -> List[Node]:
        """Returns a list of nodes of the graph."""
        return self.nodes

    def generate_label(self) -> str:
        """Returns a node label, based on the number of nodes in the tree in the form of
        A, B, C, ..., AA, AB, AC ...; note that the label is not meant to be a unique 
        identifier!"""
        return "A" * (len(self.nodes) // 26) + chr(65 + len(self.nodes) % 26)

    def add_node(self, position: Vector, radius: float, label=None) -> Node:
        """Adds a new node to the graph and returns it."""
        if label is None:
            label = self.generate_label()

        node = Node(position, radius, label)
        self.nodes.append(node)

        self.calculate_components()

        return node

    def remove_node(self, node_to_be_removed: Node):
        """Deletes a node and all of the vertices that point to it from the graph."""
        # remove the actual node from the node list
        self.get_nodes().remove(node_to_be_removed)

        # remove all of its vertices
        for node in self.get_nodes():
            if node_to_be_removed in node.neighbours:
                del node.get_neighbours()[node_to_be_removed]

        self.calculate_components()

    def add_vertex(self, n1: Node, n2: Node, weight: float = 0):
        """Adds a vertex from node n1 to node n2 (and vice versa, if it's not directed).
        Only does so if the given vertex doesn't already exist and can be added (ex.:
        if the graph is not directed and the node wants to point to itself -- we can't
        allow that."""
        if n1 is n2 and not self.directed:
            return

        # from n1 to n2
        n1.neighbours[n2] = weight

        # from n2 to n1
        if not self.directed:
            n2.neighbours[n1] = weight

        self.calculate_components()

    def does_vertex_exist(self, n1: Node, n2: Node, ignore_direction=False) -> bool:
        """Returns True if a vertex exists between the two nodes and False otherwise."""
        return n2 in n1.neighbours or (
            (not self.directed or ignore_direction) and n1 in n2.neighbours
        )

    def toggle_vertex(self, n1: Node, n2: Node):
        """Toggles a connection between to vertexes."""
        if self.does_vertex_exist(n1, n2):
            self.remove_vertex(n1, n2)
        else:
            self.add_vertex(n1, n2)

    def remove_vertex(self, n1: Node, n2: Node):
        """Removes a vertex from node n1 to node n2 (and vice versa, if it's not 
        directed). Only does so if the given vertex exists."""
        # from n1 to n2
        if n2 in n1.neighbours:
            del n1.neighbours[n2]

        # from n2 to n1
        if not self.directed and n1 in n2.neighbours:
            del n2.neighbours[n1]

        self.calculate_components()

    def complement(self):
        """Makes the graph the complement of itself."""
        for n1 in self.get_nodes():
            for n2 in self.get_nodes():
                if self.directed or id(n1) < id(n2):
                    self.toggle_vertex(n1, n2)
