"""A class for keeping track of information regarding the mouse and the keyboard."""

from dataclasses import *
from typing import *

from PyQt5.QtCore import Qt

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
    """A set of Pressable objects."""

    keys: Dict[int, Pressable] = None

    def update_state(self, key: int, value: bool) -> Optional[Pressable]:
        """Set (attempt to) key in the dictionary to a given value, returning the object
        if it succeeded and None if it doesn't."""
        if key in self.keys:
            self.keys[key].set_state(value)
            return self.keys[key]


class Keyboard(PressableCollection):
    """A class for storing information about the keyboard."""

    def __init__(self):
        # TODO: add custom config (imported from a file)

        # create special keys
        self.keys = {
            Qt.Key_Space: Pressable(),
            Qt.Key_Delete: Pressable(),
            Qt.Key_Shift: Pressable(),
        }

        # dynamically create properties for special keys...
        self.__class__.space = property(lambda self: self.keys[Qt.Key_Space])
        self.__class__.delete = property(lambda self: self.keys[Qt.Key_Delete])
        self.__class__.shift = property(lambda self: self.keys[Qt.Key_Shift])

        # ... and for letters
        for i in range(65, 91):
            self.keys[i] = Pressable()
            setattr(Keyboard, chr(i).lower(), self.keys[i])

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

        self.keys = {
            Qt.LeftButton: Pressable(),
            Qt.RightButton: Pressable(),
            Qt.MiddleButton: Pressable(),
        }

        self.position: Optional[Vector] = None  # position on canvas
        self.prev_position: Optional[Vector] = None  # previous position on canvas

        # dynamically create the properties
        self.__class__.left = property(lambda self: self.keys[Qt.LeftButton])
        self.__class__.middle = property(lambda self: self.keys[Qt.MiddleButton])
        self.__class__.right = property(lambda self: self.keys[Qt.RightButton])

    def moved_event(self, event):
        self.prev_position = self.position
        self.position = Vector(event.pos().x(), event.pos().y())

    def get_position(self):
        """Get the current mouse position."""
        if self.position is not None:
            return self.transformation.apply(self.position)

    def pressed_event(self, event):
        self.moved_event(event)
        return self.update_state(event.button(), True)

    def released_event(self, event):
        self.moved_event(event)
        return self.update_state(event.button(), False)
