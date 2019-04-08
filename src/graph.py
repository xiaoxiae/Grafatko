class Node:
    """A class for working with physical representations of nodes in a graph."""

    def __init__(self, x, y, parent, radius=20):
        """Initializes a new node."""
        # coordinates of the graph on the board
        self.x, self.y = x, y

        # list of neighbours and radius
        self.neighbours = [] if parent is None else [parent]
        self.radius = radius

        # the list of forces acting on the node
        self.forces = []

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