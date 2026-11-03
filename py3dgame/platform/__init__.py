"""Window backends and platform events."""

from .events import Event, KeyDown, KeyUp, MouseButton, MouseMove, MouseWheel, Quit, Resize, TextInput
from .window import HeadlessWindow, PygameWindow, Window, available_backends, create_window

__all__ = [
    "Event",
    "HeadlessWindow",
    "KeyDown",
    "KeyUp",
    "MouseButton",
    "MouseMove",
    "MouseWheel",
    "PygameWindow",
    "Quit",
    "Resize",
    "TextInput",
    "Window",
    "available_backends",
    "create_window",
]
