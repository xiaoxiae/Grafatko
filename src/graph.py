class Node:
    """A class for working with physical representations of nodes in a graph."""

    def __init__(self, x, y, radius):
        """Initializes a new node."""
        # coordinates of the graph on the board
        self.x, self.y = x, y

        self.neighbours = []
        self.radius = radius

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
        """Returns the radius of the node."""
        return self.neighbours

    def set_x(self, x):
        """Sets the x coordinate of the node to the specified value."""
        self.x = x

    def set_y(self, y):
        """Sets the y coordinate of the node to the specified value."""
        self.y = y

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

    def __init__(self, oriented=False):
        self.nodes = []
        self.oriented = oriented

    def is_oriented(self):
        return self.oriented

    def set_oriented(self, oriented):
        """Sets the orientation of the graph."""
        self.oriented = oriented

    def get_nodes(self):
        """Returns a list of nodes of the graph."""
        return self.nodes

    def add_node(self, x, y, radius):
        """Adds a new node to the graph and returns it."""
        node = Node(x, y, radius)
        self.nodes.append(node)

        return node

    def add_vertice(self, n1, n2):
        """Adds a vertice from node n1 to node n2 (and vice versa, if it's not oriented). Only does so if the given
        vertice doesn't already exist. Takes O(n)."""
        # from n1 to n2
        if n2 not in n1.neighbours:
            n1.neighbours.append(n2)

        # from n2 to n1
        if not self.oriented and n1 not in n2.neighbours:
            n2.neighbours.append(n1)

    def does_vertice_exist(self, n1, n2, ignore_orientation=False):
        """Returns True if a vertice exists between the two nodes and False otherwise."""
        return n2 in n1.neighbours or ((not self.oriented or ignore_orientation) and n1 in n2.neighbours)

    def remove_vertice(self, n1, n2):
        """Removes a vertice from node n1 to node n2 (and vice versa, if it's not oriented). Only does so if the given
        vertice exists. Takes O(n)."""
        # from n1 to n2
        if n2 in n1.neighbours:
            n1.neighbours.remove(n2)

        # from n2 to n1
        if not self.oriented and n1 in n2.neighbours:
            n2.neighbours.remove(n1)
