"""A class for keeping track of information regarding the mouse and the keyboard."""

from PyQt5.QtCore import Qt
from dataclasses import dataclass

from grafatko.utilities import *


@dataclass
class Pressable:
    """An object that can be pressed and released."""

    state: bool = False

    def pressed(self):
        """Return True if the Pressable is currently pressed."""
        return self.state

    def released(self):
        """Return True if the Pressable is currently released."""
        return not self.state

    def set_state(self, value: bool):
        """Update the state of the pressable."""
        self.state = value


class PressableCollection:
    """A dictionary of Pressable objects."""

    def __init__(self, keys: Sequence[Tuple[int, str]]):
        # initialize the properties and key dict
        self.keys: Dict[int, Pressable] = {}
        for key, identifier in keys:
            self.keys[key] = Pressable()
            setattr(self.__class__, identifier, self.keys[key])

    def update_state(self, key: int, value: bool) -> Optional[Pressable]:
        """(attempt to) set key in the dictionary to a given value, returning the object
        if it succeeded and None if it doesn't."""
        if key in self.keys:
            self.keys[key].set_state(value)
            return self.keys[key]


class Keyboard(PressableCollection):
    """A class for storing information about the keyboard."""

    def __init__(self):
        super().__init__(
            [
                (Qt.Key_Space, "space"),
                (Qt.Key_Delete, "delete"),
                (Qt.Key_Shift, "shift"),
            ]
            + [(i, chr(i).lower()) for i in range(65, 91)]
        )

    def pressed_event(self, event) -> Optional[Pressable]:
        """Update keyboard status when a key is pressed."""
        return self.update_state(event.key(), True)

    def released_event(self, event) -> Optional[Pressable]:
        """Update keyboard status when a key is released."""
        return self.update_state(event.key(), False)


class Mouse(PressableCollection):
    """A class for storing information about the mouse."""

    def __init__(self, transformation: Transformation):
        self.transformation = transformation  # current canvas transformation

        self.position: Optional[Vector] = None
        self.prev_position: Optional[Vector] = None
        self.last_pressed_position: Optional[Vector] = None

        super().__init__(
            [
                (Qt.LeftButton, "left"),
                (Qt.RightButton, "right"),
                (Qt.MiddleButton, "middle"),
            ]
        )

    def moved_event(self, event):
        self.prev_position = self.position
        self.position = Vector(event.pos().x(), event.pos().y())

    def current_last_distance(self):
        """Return the distance between the current mouse pos and last pressed pos."""
        return self.get_position().distance(self.last_pressed_position)

    def get_previous_position(self):
        """Get the previous mouse position."""
        if self.prev_position is not None:
            return self.transformation.apply(self.prev_position)

    def get_position(self):
        """Get the current mouse position."""
        if self.position is not None:
            return self.transformation.apply(self.position)

    def pressed_event(self, event):
        self.moved_event(event)
        key = self.update_state(event.button(), True)

        # sneakily update the last pressed position before returning the key
        if key is self.left:
            self.last_pressed_position = self.get_position()

        return key

    def released_event(self, event):
        self.moved_event(event)
        return self.update_state(event.button(), False)
