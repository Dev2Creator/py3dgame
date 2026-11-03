"""Rigid bodies and their shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Union

from ..math3d import Vec2


@dataclass(frozen=True)
class Circle:
    radius: float

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError("circle radius must be positive")

    def half_extents(self) -> Tuple[float, float]:
        return self.radius, self.radius


@dataclass(frozen=True)
class Box:
    half_width: float
    half_height: float

    def __post_init__(self) -> None:
        if self.half_width <= 0 or self.half_height <= 0:
            raise ValueError("box half extents must be positive")

    def half_extents(self) -> Tuple[float, float]:
        return self.half_width, self.half_height


Shape = Union[Circle, Box]


@dataclass
class Body:
    """A 2D rigid body. Static bodies never move and have infinite mass."""

    shape: Shape
    position: Vec2 = field(default_factory=Vec2)
    velocity: Vec2 = field(default_factory=Vec2)
    mass: float = 1.0
    restitution: float = 0.2
    friction: float = 0.4
    gravity_scale: float = 1.0
    static: bool = False
    layer: int = 1
    mask: int = 0xFFFFFFFF
    is_trigger: bool = False
    linear_damping: float = 0.0
    name: str = ""
    force: Vec2 = field(default_factory=Vec2)
    previous_position: Vec2 | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.position, Vec2):
            self.position = Vec2(*self.position)
        if not isinstance(self.velocity, Vec2):
            self.velocity = Vec2(*self.velocity)
        if not isinstance(self.force, Vec2):
            self.force = Vec2(*self.force)
        if self.previous_position is not None and not isinstance(self.previous_position, Vec2):
            self.previous_position = Vec2(*self.previous_position)
        if self.mass <= 0 and not self.static:
            raise ValueError("dynamic bodies need a positive mass")
        if not 0.0 <= self.restitution <= 1.0:
            raise ValueError("restitution must be within 0..1")
        if not 0.0 <= self.friction <= 1.0:
            raise ValueError("friction must be within 0..1")
        if self.linear_damping < 0:
            raise ValueError("linear damping must not be negative")
        if self.layer == 0:
            raise ValueError("layer 0 is reserved for 'nothing'")

    @property
    def inv_mass(self) -> float:
        return 0.0 if self.static else 1.0 / self.mass

    def apply_force(self, vector: Vec2) -> None:
        if not self.static:
            self.force = self.force + vector

    def apply_impulse(self, impulse: Vec2) -> None:
        if not self.static:
            self.velocity = self.velocity + impulse * self.inv_mass

    def aabb(self) -> Tuple[float, float, float, float]:
        half_x, half_y = self.shape.half_extents()
        return (
            self.position.x - half_x,
            self.position.y - half_y,
            self.position.x + half_x,
            self.position.y + half_y,
        )

    def contains_point(self, point: Vec2) -> bool:
        if isinstance(self.shape, Circle):
            delta = point - self.position
            return delta.length_squared() <= self.shape.radius ** 2
        return (
            abs(point.x - self.position.x) <= self.shape.half_width
            and abs(point.y - self.position.y) <= self.shape.half_height
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        label = self.name or type(self.shape).__name__.lower()
        return f"Body({label} at {self.position.x:.1f},{self.position.y:.1f})"
