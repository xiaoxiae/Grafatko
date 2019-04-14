class Node:
    """A class for working with physical representations of nodes in a graph."""

    def __init__(self, x, y, radius, label=None):
        """Initializes a new node."""
        # coordinates and radius of the graph on a plane
        self.x, self.y = x, y
        self.radius = radius

        # the label that will be displayed
        self.label = label

        # neighbours of the node
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
        """Evaluates all of the forces acting upon the node, moving it accordingly."""
        xd, yd = 0, 0
        while len(self.forces) != 0:
            force = self.forces.pop()
            xd += force[0]
            yd += force[1]

        self.x += xd
        self.y += yd


class Graph:
    """A class for working with physical representations of a graph."""

    def __init__(self, oriented=False, weighted=False):
        self.nodes = []
        self.oriented = oriented
        self.weighted = weighted

    def is_oriented(self):
        """Returns True if the graph is oriented and False otherwise."""
        return self.oriented

    def set_oriented(self, oriented):
        """Sets the orientation of the graph."""
        # if we are converting from oriented, we need to change all of the vertices to go both ways
        if not oriented:
            self._convert_from_oriented()

        self.oriented = oriented

    def is_weighted(self):
        """Returns True if the graph is weighted and False otherwise."""
        return self.weighted

    def set_weighted(self, weighted):
        """Sets, whether the graph is weighted or not."""
        self.weighted = weighted

    def _convert_from_oriented(self):
        """Converts each of the vertices of the graph to go both ways. Takes O(number of nodes * number of vertices)."""
        for node in self.get_nodes():
            for neighbour in node.get_neighbours():
                self.add_vertex(neighbour, node, weight=0)

    def get_nodes(self):
        """Returns a list of nodes of the graph."""
        return self.nodes

    def __len__(self):
        """Define a length of the graph object as the number of nodes."""
        return len(self.get_nodes())

    def generate_label(self):
        """Returns a node label, based on the number of nodes in the tree in the form of A, B, C, ..., AA, AB, AC ...
        Note that the label is not meant to be an unique identifier!"""
        n = self.__len__()
        label = "A" * (n // 26) + chr(65 + n % 26)

        return label

    def add_node(self, x, y, radius, name=None):
        """Adds a new node to the graph and returns it."""
        node = Node(x, y, radius, name if name is not None else self.generate_label())
        self.nodes.append(node)

        return node

    def delete_node(self, node_to_remove):
        """Deletes a node and all of the vertices that point to it from the graph. Takes O(number of vertices)"""
        # remove the actual node
        self.get_nodes().remove(node_to_remove)

        # remove all of its vertices
        for node in self.get_nodes():
            if node_to_remove in node.neighbours:
                del node.get_neighbours()[node_to_remove]

    def add_vertex(self, n1, n2, weight=0):
        """Adds a vertex from node n1 to node n2 (and vice versa, if it's not oriented). Only does so if the given
        vertex doesn't already exist. Takes O(number of nodes)."""
        # from n1 to n2
        n1.neighbours[n2] = weight

        # from n2 to n1
        if not self.oriented:
            n2.neighbours[n1] = weight

    def does_vertex_exist(self, n1, n2, ignore_orientation=False):
        """Returns True if a vertex exists between the two nodes and False otherwise. Takes O(number of nodes)."""
        return n2 in n1.neighbours or ((not self.oriented or ignore_orientation) and n1 in n2.neighbours)

    def remove_vertex(self, n1, n2):
        """Removes a vertex from node n1 to node n2 (and vice versa, if it's not oriented). Only does so if the given
        vertex exists. Takes O(number of nodes)."""
        # from n1 to n2
        if n2 in n1.neighbours:
            del n1.neighbours[n2]

        # from n2 to n1
        if not self.oriented and n1 in n2.neighbours:
            del n2.neighbours[n1]
