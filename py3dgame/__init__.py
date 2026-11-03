"""py3dgame: a Python-native game library.

Release 0.3.0 covers the runtime foundation, a 2D toolchain and an atmosphere
layer:

* window backends (headless, optional pygame/SDL2)
* fixed-timestep loop and input
* scene graph and transform maths
* PNG images, sprites, sheets, animation
* additive 2D lighting
* 2D rigid-body physics with raycasts and layers
* Dunia-inspired world systems: day/night clock, fire spread, destruction
* Atmosphere: procedural sky, density fog, lightning, water reflections and
  per-pixel post-processing shaders

3D rendering, skeletal animation, audio and the editor are not implemented and
are not exported.
"""

from __future__ import annotations

__version__ = "0.3.0"

from .core.game import Game
from .core.scene import Node, Scene, Transform
from .exceptions import (
    AssetNotFoundError,
    BackendError,
    ConfigurationError,
    ImageFormatError,
    Py3DGameError,
    SceneError,
)
from .input.manager import InputState
from .math3d import Mat4, Vec2, Vec3
from .physics.body import Body, Box, Circle
from .physics.collision import Manifold, collide
from .physics.world import Contact, PhysicsWorld, RayHit
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
from .platform.window import HeadlessWindow, PygameWindow, Window, available_backends, create_window
from .renderer2d.canvas import Canvas
from .renderer2d.fog import Fog, FogSettings
from .renderer2d.lightning import Lightning
from .renderer2d.reflection import WaterSurface
from .renderer2d.shader import (
    PixelShader,
    Shader,
    ShaderStack,
    grayscale,
    posterize,
    scanlines,
    tint,
    vignette,
)
from .renderer2d.sky import Sky, SkySettings
from .renderer2d.image import Image
from .renderer2d.lighting2d import AmbientLight, Light2D, LightMap, build_lightmap
from .renderer2d.sprite import Animation, AnimatedSprite, Sprite, SpriteSheet
from .world.daynight import DayNightCycle, SunState
from .world.destruction import Destructible, DestructionSystem
from .world.fire import BURNING, BURNT, UNBURNT, FireGrid, FireStats

__all__ = [
    "Fog",
    "FogSettings",
    "Lightning",
    "PixelShader",
    "Shader",
    "ShaderStack",
    "Sky",
    "SkySettings",
    "WaterSurface",
    "grayscale",
    "posterize",
    "scanlines",
    "tint",
    "vignette",
    "AmbientLight",
    "AnimatedSprite",
    "Animation",
    "AssetNotFoundError",
    "BackendError",
    "Body",
    "Box",
    "BURNING",
    "BURNT",
    "Canvas",
    "Circle",
    "ConfigurationError",
    "Contact",
    "DayNightCycle",
    "Destructible",
    "DestructionSystem",
    "Event",
    "FireGrid",
    "FireStats",
    "Game",
    "HeadlessWindow",
    "Image",
    "ImageFormatError",
    "InputState",
    "KeyDown",
    "KeyUp",
    "Light2D",
    "LightMap",
    "Manifold",
    "Mat4",
    "MouseButton",
    "MouseMove",
    "MouseWheel",
    "Node",
    "PhysicsWorld",
    "Py3DGameError",
    "PygameWindow",
    "Quit",
    "RayHit",
    "Resize",
    "Scene",
    "SceneError",
    "Sprite",
    "SpriteSheet",
    "SunState",
    "TextInput",
    "Transform",
    "UNBURNT",
    "Vec2",
    "Vec3",
    "Window",
    "__version__",
    "available_backends",
    "build_lightmap",
    "collide",
    "create_window",
]
