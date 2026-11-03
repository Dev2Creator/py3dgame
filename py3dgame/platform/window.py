"""Window backends.

``headless`` is always available and is what CI and servers use. ``pygame``
provides a real OS window, and is an optional dependency:

    pip install "py3dgame[window]"
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, List, Optional

from ..exceptions import BackendError, ConfigurationError
from .events import (
    Event,
    KeyDown,
    KeyUp,
    MouseButton,
    MouseMove,
    MouseWheel,
    Quit,
    Resize,
    TextInput,
)

__all__ = ["Window", "HeadlessWindow", "PygameWindow", "create_window", "BACKENDS"]

BACKENDS = ("auto", "headless", "pygame")


class Window(ABC):
    """A platform surface plus the events it produced since the last poll."""

    def __init__(self, title: str, width: int, height: int) -> None:
        if int(width) <= 0 or int(height) <= 0:
            raise ConfigurationError("window width and height must be positive")
        self._title = str(title)
        self._width = int(width)
        self._height = int(height)
        self._closed = False
        self.frame_count = 0

    @property
    def title(self) -> str:
        return self._title

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def closed(self) -> bool:
        return self._closed

    def set_title(self, title: str) -> None:
        self._title = str(title)

    @abstractmethod
    def poll_events(self) -> List[Event]:
        ...

    @abstractmethod
    def present(self, canvas) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class HeadlessWindow(Window):
    """An in-memory window: no OS surface, but a real event queue and framebuffer."""

    def __init__(self, title: str = "py3dgame", width: int = 1280, height: int = 720) -> None:
        super().__init__(title, width, height)
        self._events: Deque[Event] = deque()
        self.last_canvas = None

    def post(self, event: Event) -> None:
        """Queue an event, used by tests and by scripted input playback."""
        self._events.append(event)

    def resize(self, width: int, height: int) -> None:
        self._width, self._height = int(width), int(height)
        self._events.append(Resize(width=self._width, height=self._height))

    def poll_events(self) -> List[Event]:
        events = list(self._events)
        self._events.clear()
        return events

    def present(self, canvas) -> None:
        if self._closed:
            raise BackendError("cannot present to a closed window")
        self.last_canvas = canvas
        self.frame_count += 1

    def close(self) -> None:
        self._closed = True


class PygameWindow(Window):
    """Real window and GPU-backed presentation through SDL2 (via pygame)."""

    def __init__(self, title: str = "py3dgame", width: int = 1280, height: int = 720) -> None:
        super().__init__(title, width, height)
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise BackendError(
                'the pygame window backend needs the optional dependency: '
                'pip install "py3dgame[window]"'
            ) from exc

        self._pygame = pygame
        try:
            pygame.display.init()
            self._display_surface = pygame.display.set_mode((self._width, self._height))
        except Exception as exc:  # SDL raises several unrelated exception types
            raise BackendError(f"could not create a window: {exc}") from exc
        pygame.display.set_caption(self._title)

    def set_title(self, title: str) -> None:
        super().set_title(title)
        self._pygame.display.set_caption(self._title)

    def poll_events(self) -> List[Event]:
        pg = self._pygame
        out: List[Event] = []
        for event in pg.event.get():
            if event.type == pg.QUIT:
                out.append(Quit())
            elif event.type == pg.KEYDOWN:
                out.append(KeyDown(key=_key_name(event.key)))
            elif event.type == pg.KEYUP:
                out.append(KeyUp(key=_key_name(event.key)))
            elif event.type == pg.TEXTINPUT:
                out.append(TextInput(text=event.text))
            elif event.type == pg.MOUSEMOTION:
                out.append(MouseMove(x=float(event.pos[0]), y=float(event.pos[1])))
            elif event.type == pg.MOUSEBUTTONDOWN:
                out.append(MouseButton(button=event.button, pressed=True,
                                       x=float(event.pos[0]), y=float(event.pos[1])))
            elif event.type == pg.MOUSEBUTTONUP:
                out.append(MouseButton(button=event.button, pressed=False,
                                       x=float(event.pos[0]), y=float(event.pos[1])))
            elif event.type == pg.MOUSEWHEEL:
                out.append(MouseWheel(dy=float(event.y)))
            elif event.type == pg.VIDEORESIZE:
                self._width, self._height = int(event.w), int(event.h)
                out.append(Resize(width=self._width, height=self._height))
        return out

    def present(self, canvas) -> None:
        if self._closed:
            raise BackendError("cannot present to a closed window")
        pg = self._pygame
        frame = pg.image.frombuffer(canvas.surface, canvas.size, "RGBA")
        self._display_surface.blit(frame, (0, 0))
        pg.display.flip()
        self.frame_count += 1

    def close(self) -> None:
        if not self._closed:
            self._pygame.display.quit()
            self._closed = True


def _key_name(key: int) -> str:
    """Normalise a backend key code to a stable lowercase name."""
    try:
        import pygame

        name = pygame.key.name(key) or str(key)
    except Exception:  # pragma: no cover - defensive
        name = str(key)
    return name.strip().lower().replace(" ", "_")


def create_window(title: str = "py3dgame", width: int = 1280, height: int = 720,
                  backend: str = "auto") -> Window:
    """Create a window using ``backend`` or the best available one.

    ``auto`` prefers a real window and falls back to headless when no display
    is available, which keeps servers and CI working without configuration.
    """
    if backend not in BACKENDS:
        raise ConfigurationError(
            f"unknown window backend {backend!r}; expected one of {', '.join(BACKENDS)}"
        )
    if backend == "headless":
        return HeadlessWindow(title, width, height)
    if backend == "pygame":
        return PygameWindow(title, width, height)
    if os.environ.get("PY3DGAME_WINDOW", "").lower() == "headless":
        return HeadlessWindow(title, width, height)
    if not display_is_available():
        # No display server: SDL can still create an off-screen surface, but
        # nothing would ever be shown or receive input, so headless is honest.
        return HeadlessWindow(title, width, height)
    try:
        return PygameWindow(title, width, height)
    except BackendError:
        return HeadlessWindow(title, width, height)


def available_backends() -> List[str]:
    """Which backends can actually be constructed in this environment."""
    found = ["headless"]
    try:
        import pygame  # noqa: F401

        found.append("pygame")
    except ImportError:
        pass
    return found


def display_is_available() -> bool:
    """True when a real window can probably be opened (POSIX DISPLAY check)."""
    if os.name == "nt":
        return True
    if hasattr(os, "uname") and os.uname().sysname == "Darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
                or os.environ.get("SDL_VIDEODRIVER"))
