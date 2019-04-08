class Node:
    """A class for working with physical representations of nodes in a graph."""

    def __init__(self, x, y, radius=20):
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

    def __init__(self):
        self.nodes = []

    def get_nodes(self):
        """Returns a list of nodes of the graph."""
        return self.nodes

    def add_node(self, x, y):
        """Adds a new node to the graph and returns it."""
        node = Node(x, y)
        self.nodes.append(node)

        return node

    def add_vertice(self, n1, n2):
        """Adds a vertice from node n1 to node n2. Only does so if the given vertice doesn't already exist.
        Takes O(n)."""
        if n1 not in n2.neighbours:
            n2.neighbours.append(n1)

        if n2 not in n1.neighbours:
            n1.neighbours.append(n2)

    def does_vertice_exist(self, n1, n2):
        """Returns True if a vertice exists between the two nodes and False otherwise."""
        return n1 in n2.neighbours and n2 in n1.neighbours

    def remove_vertice(self, n1, n2):
        """Removes a vertice from node n1 to node n2. Only does so if the given vertice exists. Takes O(n)."""
        if n1 in n2.neighbours:
            n2.neighbours.remove(n1)

        if n2 in n1.neighbours:
            n1.neighbours.remove(n2)
