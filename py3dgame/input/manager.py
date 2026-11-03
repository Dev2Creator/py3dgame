"""Keyboard, mouse and action state.

Frame semantics: ``was_pressed`` is true only during the frame the key went down,
``is_down`` stays true while it is held. ``end_frame`` clears the per-frame sets,
so the game loop calls it after drawing.
"""

from __future__ import annotations

from typing import Callable, Dict, FrozenSet, List, Set

from ..exceptions import ConfigurationError
from ..math3d import Vec2
from ..platform.events import (
    Event,
    KeyDown,
    KeyUp,
    MouseButton,
    MouseMove,
    MouseWheel,
)

__all__ = ["InputState"]

Callback = Callable[[str], None]


def _normalise(key: str) -> str:
    if not isinstance(key, str) or not key.strip():
        raise ConfigurationError("key names must be non-empty strings")
    return key.strip().lower().replace("-", "_").replace(" ", "_")


class InputState:
    """Tracks raw device state and named actions bound to keys."""

    def __init__(self) -> None:
        self._down: Set[str] = set()
        self._pressed: Set[str] = set()
        self._released: Set[str] = set()
        self._buttons: Set[int] = set()
        self._buttons_pressed: Set[int] = set()
        self._buttons_released: Set[int] = set()
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.wheel_dy = 0.0
        self._actions: Dict[str, FrozenSet[str]] = {}
        self._key_callbacks: Dict[str, List[Callback]] = {}
        self._action_callbacks: Dict[str, List[Callback]] = {}

    # -- bindings ---------------------------------------------------- #
    def bind_action(self, name: str, *keys: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ConfigurationError("action name must be a non-empty string")
        if not keys:
            raise ConfigurationError(f"action {name!r} needs at least one key")
        self._actions[name] = frozenset(_normalise(key) for key in keys)

    def action_keys(self, name: str) -> FrozenSet[str]:
        if name not in self._actions:
            raise ConfigurationError(f"unknown action {name!r}")
        return self._actions[name]

    def on_key_press(self, key: str, callback: Callback) -> None:
        self._key_callbacks.setdefault(_normalise(key), []).append(callback)

    def on_action_press(self, action: str, callback: Callback) -> None:
        self._action_callbacks.setdefault(action, []).append(callback)

    # -- event ingestion --------------------------------------------- #
    def handle_event(self, event: Event) -> None:
        if isinstance(event, KeyDown):
            key = _normalise(event.key)
            if key in self._down:
                return  # OS key-repeat: state is already down, do not re-fire
            self._pressed.add(key)
            self._down.add(key)
            self._fire(key)
        elif isinstance(event, KeyUp):
            key = _normalise(event.key)
            self._down.discard(key)
            self._released.add(key)
        elif isinstance(event, MouseMove):
            self.mouse_x, self.mouse_y = float(event.x), float(event.y)
        elif isinstance(event, MouseButton):
            button = int(event.button)
            self.mouse_x, self.mouse_y = float(event.x), float(event.y)
            if event.pressed:
                if button not in self._buttons:
                    self._buttons_pressed.add(button)
                self._buttons.add(button)
            else:
                self._buttons.discard(button)
                self._buttons_released.add(button)
        elif isinstance(event, MouseWheel):
            self.wheel_dy += float(event.dy)

    def _fire(self, key: str) -> None:
        for callback in self._key_callbacks.get(key, ()):
            callback(key)
        for action, keys in self._actions.items():
            if key in keys:
                for callback in self._action_callbacks.get(action, ()):
                    callback(action)

    def end_frame(self) -> None:
        self._pressed.clear()
        self._released.clear()
        self._buttons_pressed.clear()
        self._buttons_released.clear()
        self.wheel_dy = 0.0

    # -- queries ------------------------------------------------------ #
    def is_down(self, key: str) -> bool:
        return _normalise(key) in self._down

    def was_pressed(self, key: str) -> bool:
        return _normalise(key) in self._pressed

    def was_released(self, key: str) -> bool:
        return _normalise(key) in self._released

    def action_down(self, name: str) -> bool:
        return bool(self.action_keys(name) & self._down)

    def action_pressed(self, name: str) -> bool:
        return bool(self.action_keys(name) & self._pressed)

    def action_released(self, name: str) -> bool:
        return bool(self.action_keys(name) & self._released)

    def mouse_position(self) -> Vec2:
        return Vec2(self.mouse_x, self.mouse_y)

    def button_down(self, button: int = 1) -> bool:
        return int(button) in self._buttons

    def button_pressed(self, button: int = 1) -> bool:
        return int(button) in self._buttons_pressed

    @property
    def pressed_keys(self) -> FrozenSet[str]:
        return frozenset(self._pressed)

    @property
    def held_keys(self) -> FrozenSet[str]:
        return frozenset(self._down)
