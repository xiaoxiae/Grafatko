"""A class for keeping track of information regarding the mouse and the keyboard."""

from dataclasses import *
from typing import *

from PyQt5.QtCore import Qt

from utilities import *


@dataclass
class Pressable:
    state: bool = False

    def pressed(self):
        """Return True if the Pressable is currently pressed. Prevents sending two press
        events in a row."""
        return self.state

    def released(self):
        """Return True if the Pressable is currently released. Prevents sending two
        release events in a row."""
        return not self.state

    def update_state(self, value: bool):
        """Update the state of the pressable."""
        self.state = value


class Keyboard:
    """A class for storing information about the keyboard."""

    def __init__(self):
        self.keys: Dict[int, bool] = {
            Qt.Key_Space: Pressable(),
            Qt.Key_Delete: Pressable(),
            Qt.Key_Shift: Pressable(),
        }

        # TODO: add custom config (imported from a file)

        # dynamically create properties for special keys...
        self.__class__.space = property(lambda self: self.keys[Qt.Key_Space])
        self.__class__.delete = property(lambda self: self.keys[Qt.Key_Delete])
        self.__class__.shift = property(lambda self: self.keys[Qt.Key_Shift])

        # ... and for letters
        for i in range(65, 91):
            self.keys[i] = Pressable()
            setattr(Keyboard, chr(i).lower(), self.keys[i])

    def __set_key(self, key: int, value: bool) -> Optional[Pressable]:
        """Set (attempt to) key in the dictionary to a given value, returning the object
        if it succeeded."""
        if key in self.keys:
            self.keys[key].update_state(value)
            return self.keys[key]

    def pressed_event(self, event) -> Optional[Pressable]:
        """Update keyboard status when a key is pressed."""
        return self.__set_key(event.key(), True)

    def released_event(self, event) -> Optional[Pressable]:
        """Update keyboard status when a key is released."""
        return self.__set_key(event.key(), False)


@dataclass
class MouseButtonState(Pressable):
    """An object representing the state of a mouse button."""

    # TODO: getters and setters
    last_pressed: Optional[Vector] = None  # last position where it was pressed
    last_released: Optional[Vector] = None  # last position where it was released


class Mouse:
    """A class for storing information about the mouse."""

    def __init__(self, transformation: Transformation):
        self.transformation = transformation  # current canvas transformation

        self.buttons: Dict[int, bool] = {
            Qt.LeftButton: MouseButtonState(),
            Qt.RightButton: MouseButtonState(),
            Qt.MiddleButton: MouseButtonState(),
        }

        self.position: Optional[Vector] = None  # position on canvas
        self.prev_position: Optional[Vector] = None  # previous position on canvas

        # dynamically create the properties
        self.__class__.left = property(lambda self: self.buttons[Qt.LeftButton])
        self.__class__.middle = property(lambda self: self.buttons[Qt.MiddleButton])
        self.__class__.right = property(lambda self: self.buttons[Qt.RightButton])

    def moved_event(self, event):
        self.prev_position = self.position
        self.position = Vector(event.pos().x(), event.pos().y())

    def get_position(self):
        """Get the current mouse position."""
        return self.transformation.apply(self.position)

    def get_previous_position(self):
        """Get the previous mouse position."""
        return self.transformation.apply(self.prev_position)

    def __set_button(
        self, button: int, position: Vector, value: bool
    ) -> MouseButtonState:
        """Set (attempt to) button in the dictionary to a given value."""
        if button in self.buttons:
            # TODO getters and setters
            if value:
                self.buttons[button].last_pressed = position
            else:
                self.buttons[button].last_released = position

            self.buttons[button].update_state(value)

            return self.buttons[button]

    def pressed_event(self, event):
        self.moved_event(event)
        return self.__set_button(event.button(), self.get_position(), True)

    def released_event(self, event):
        self.moved_event(event)
        return self.__set_button(event.button(), self.get_position(), False)
