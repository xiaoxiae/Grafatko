class Node:
    """A class for working with physical representations of nodes in a graph."""

    def __init__(self, x, y, radius, label=None):
        """Initializes a new node."""
        # coordinates and radius of the node on the canvas
        self.x, self.y = x, y
        self.radius = radius

        # the label that will be displayed
        self.label = label

        # neighbours of the node (ie. vertices)
        self.neighbours = {}

        # the list of forces acting on the node
        self.forces = []

    def get_x(self):
        """Returns the x coordinate of the node."""
        return self.x

    def get_y(self):
        """Returns the y coordinate of the node."""
        return self.y

    def get_radius(self):
        """Returns the radius of the node."""
        return self.radius

    def get_neighbours(self):
        """Returns the neighbours of the node."""
        return self.neighbours

    def get_label(self):
        """Returns the label of the node."""
        return self.label

    def set_x(self, x):
        """Sets the x coordinate of the node to the specified value."""
        self.x = x

    def set_y(self, y):
        """Sets the y coordinate of the node to the specified value."""
        self.y = y

    def set_label(self, label):
        """Sets the label of the node to the specified value."""
        self.label = label

    def add_force(self, force):
        """Adds a force that is acting upon the node to the force list."""
        self.forces.append(force)

    def evaluate_forces(self):
        """Evaluates all of the forces acting upon the node and moves it accordingly."""
        xd, yd = 0, 0
        while len(self.forces) != 0:
            force = self.forces.pop()
            xd += force[0]
            yd += force[1]

        self.x += xd
        self.y += yd


class Graph:
    """A class for working with graphs."""

    def __init__(self, directed=False, weighted=False):
        self.nodes = []
        self.directed = directed
        self.weighted = weighted

        # for storing sets of nodes that are connected to each other
        # helpful for calculating forces and moving connected nodes
        self.continuity_sets = []

    def calculate_continuity_sets(self):
        """Calculates sets of nodes that are connected."""
        self.continuity_sets = []

        for node in self.nodes:
            # the current set of nodes that we know are reachable from one another
            working_set = set([node] + list(node.get_neighbours()))

            # the index of the set that we added the working set to
            set_index = None

            i = 0
            while i < len(self.continuity_sets):
                existing_set = self.continuity_sets[i]

                # if an intersection exists, perform set union
                if len(existing_set.intersection(working_set)) != 0:
                    # if this is the first set to be merged, don't pop it from the list
                    # if we have already merged a set, it means that the working set joined two already existing sets
                    if set_index is None:
                        existing_set |= working_set
                        set_index = i
                        i += 1
                    else:
                        existing_set |= self.continuity_sets.pop(set_index)
                        set_index = i - 1
                else:
                    i += 1

            # if we haven't performed any set merges, add the set to the continuity sets
            if set_index is None:
                self.continuity_sets.append(working_set)

    def share_continuity_set(self, n1, n2):
        """Returns True if both of the nodes are in the same continuity set."""
        for continuity_set in self.continuity_sets:
            n1_in_s, n2_in_s = n1 in continuity_set, n2 in continuity_set

            # if both are in one set, we know for certain that they share a set
            # if only one is in a set, we know for certain that they can't share a set
            # otherwise, we can't be sure and have to check additional sets
            if n1_in_s and n2_in_s:
                return True
            elif n1_in_s or n2_in_s:
                return False

    def is_directed(self):
        """Returns True if the graph is directed and False otherwise."""
        return self.directed

    def set_directed(self, directed):
        """Sets, whether the graph is directed or not."""
        # if we are converting from a directed graph, we need to change all of the vertices to go both ways
        if not directed:
            self._make_vertices_both_ways()

        self.directed = directed

    def _make_vertices_both_ways(self):
        """Converts each of the vertices of the graph to go both ways. Takes O(number of nodes * number of vertices)."""
        for node in self.get_nodes():
            for neighbour in node.get_neighbours():
                self.add_vertex(neighbour, node, weight=0)

    def is_weighted(self):
        """Returns True if the graph is weighted and False otherwise."""
        return self.weighted

    def set_weighted(self, weighted):
        """Sets, whether the graph is weighted or not."""
        self.weighted = weighted

    def get_weight(self, n1, n2):
        """Returns the weight of the specified vertex and None, if it doesn't exist."""
        return None if not self.does_vertex_exist(n1, n2) else self.nodes[self.nodes.index(n1)].neighbours[n2]

    def get_nodes(self):
        """Returns a list of nodes of the graph."""
        return self.nodes

    def generate_label(self):
        """Returns a node label, based on the number of nodes in the tree in the form of A, B, C, ..., AA, AB, AC ...
        Note that the label is not meant to be a unique identifier!"""
        n = len(self.nodes)
        label = "A" * (n // 26) + chr(65 + n % 26)

        return label

    def add_node(self, x, y, radius, name=None):
        """Adds a new node to the graph and returns it."""
        node = Node(x, y, radius, name if name is not None else self.generate_label())
        self.nodes.append(node)

        self.calculate_continuity_sets()

        return node

    def remove_node(self, node_to_remove):
        """Deletes a node and all of the vertices that point to it from the graph."""
        # remove the actual node from the node list
        self.get_nodes().remove(node_to_remove)

        # remove all of its vertices
        for node in self.get_nodes():
            if node_to_remove in node.neighbours:
                del node.get_neighbours()[node_to_remove]

        self.calculate_continuity_sets()

    def add_vertex(self, n1, n2, weight=0):
        """Adds a vertex from node n1 to node n2 (and vice versa, if it's not directed). Only does so if the given
        vertex doesn't already exist."""
        # from n1 to n2
        n1.neighbours[n2] = weight

        # from n2 to n1
        if not self.directed:
            n2.neighbours[n1] = weight

        self.calculate_continuity_sets()

    def does_vertex_exist(self, n1, n2, ignore_direction=False):
        """Returns True if a vertex exists between the two nodes and False otherwise."""
        return n2 in n1.neighbours or ((not self.directed or ignore_direction) and n1 in n2.neighbours)

    def remove_vertex(self, n1, n2):
        """Removes a vertex from node n1 to node n2 (and vice versa, if it's not directed). Only does so if the given
        vertex exists."""
        # from n1 to n2
        if n2 in n1.neighbours:
            del n1.neighbours[n2]

        # from n2 to n1
        if not self.directed and n1 in n2.neighbours:
            del n2.neighbours[n1]

        self.calculate_continuity_sets()
