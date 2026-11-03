"""Platform events.

Events are plain immutable dataclasses so they can be logged, replayed in tests
and translated by any window backend without the engine depending on it.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Event",
    "KeyDown",
    "KeyUp",
    "TextInput",
    "MouseMove",
    "MouseButton",
    "MouseWheel",
    "Resize",
    "Quit",
]


@dataclass(frozen=True)
class Event:
    """Base class for everything the engine receives from a window."""

    timestamp: float = 0.0


@dataclass(frozen=True)
class KeyDown(Event):
    key: str = ""


@dataclass(frozen=True)
class KeyUp(Event):
    key: str = ""


@dataclass(frozen=True)
class TextInput(Event):
    text: str = ""


@dataclass(frozen=True)
class MouseMove(Event):
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True)
class MouseButton(Event):
    button: int = 0
    pressed: bool = True
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True)
class MouseWheel(Event):
    dy: float = 0.0


@dataclass(frozen=True)
class Resize(Event):
    width: int = 0
    height: int = 0


@dataclass(frozen=True)
class Quit(Event):
    """The user asked to close the window."""
