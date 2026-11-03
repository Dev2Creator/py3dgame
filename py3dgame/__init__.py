"""py3dgame — create games, write Python.

A Python-native game library. This release ships the runtime foundation:
window + fixed-timestep loop, input with action bindings, a scene graph with
real transforms, and a software 2D rasteriser.

    import py3dgame as p3d

    game = p3d.Game("My Game", 960, 540)
    scene = p3d.Scene("Main")
    scene.add(p3d.Node("player", position=p3d.Vec3(0, 0, 0)))
    game.load_scene(scene)
    game.run()
"""

from __future__ import annotations

from .core.game import Game
from .core.scene import Node, Scene, Transform
from .exceptions import (
    AssetNotFoundError,
    BackendError,
    ConfigurationError,
    Py3DGameError,
    SceneError,
)
from .input.manager import InputState
from .math3d import Mat4, Vec2, Vec3
from .platform import events
from .platform.events import (
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
from .platform.window import (
    HeadlessWindow,
    PygameWindow,
    Window,
    available_backends,
    create_window,
)
from .renderer2d.canvas import Canvas

__version__ = "0.1.0"

__all__ = [
    "AssetNotFoundError",
    "BackendError",
    "Canvas",
    "ConfigurationError",
    "Event",
    "Game",
    "HeadlessWindow",
    "InputState",
    "KeyDown",
    "KeyUp",
    "Mat4",
    "MouseButton",
    "MouseMove",
    "MouseWheel",
    "Node",
    "Py3DGameError",
    "PygameWindow",
    "Quit",
    "Resize",
    "Scene",
    "SceneError",
    "TextInput",
    "Transform",
    "Vec2",
    "Vec3",
    "Window",
    "__version__",
    "available_backends",
    "create_window",
    "events",
]
