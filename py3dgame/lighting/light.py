"""Lights for the 3D pipeline. The 2D lights live in renderer2d and are separate."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from ..math3d import Vec3


def _validate_colour(colour: Tuple[int, int, int]) -> Tuple[int, int, int]:
    if len(colour) != 3 or any(not 0 <= int(c) <= 255 for c in colour):
        raise ValueError("light colour must be three channels between 0 and 255")
    return (int(colour[0]), int(colour[1]), int(colour[2]))


@dataclass(frozen=True)
class DirectionalLight:
    direction: Vec3 = Vec3(0.35, -1.0, -0.45)
    colour: Tuple[int, int, int] = (255, 244, 226)
    intensity: float = 1.0

    def __post_init__(self) -> None:
        if self.direction.length() == 0.0:
            raise ValueError("a directional light needs a direction")
        if self.intensity < 0.0:
            raise ValueError("light intensity cannot be negative")
        object.__setattr__(self, "colour", _validate_colour(self.colour))

    @property
    def unit_direction(self) -> Vec3:
        """Direction the light travels in, normalised."""
        return self.direction.normalized()


@dataclass(frozen=True)
class PointLight:
    position: Vec3 = Vec3(0.0, 2.0, 0.0)
    colour: Tuple[int, int, int] = (255, 236, 210)
    intensity: float = 8.0
    reach: float = 12.0

    def __post_init__(self) -> None:
        if self.intensity < 0.0:
            raise ValueError("light intensity cannot be negative")
        if self.reach <= 0.0:
            raise ValueError("point light reach must be positive")
        object.__setattr__(self, "colour", _validate_colour(self.colour))

    def attenuation(self, distance: float) -> float:
        if distance >= self.reach:
            return 0.0
        ratio = distance / self.reach
        return (1.0 - ratio) ** 2 / (1.0 + distance * distance * 0.25)


@dataclass(frozen=True)
class SpotLight:
    position: Vec3 = Vec3(0.0, 4.0, 1.0)
    direction: Vec3 = Vec3(0.0, -1.0, -0.2)
    colour: Tuple[int, int, int] = (255, 240, 220)
    intensity: float = 10.0
    reach: float = 16.0
    inner_degrees: float = 18.0
    outer_degrees: float = 34.0

    def __post_init__(self) -> None:
        if self.direction.length() == 0.0:
            raise ValueError("a spotlight needs a direction")
        if not 0.0 < self.inner_degrees < self.outer_degrees < 90.0:
            raise ValueError("spotlight cone must satisfy 0 < inner < outer < 90")
        if self.intensity < 0.0:
            raise ValueError("light intensity cannot be negative")
        if self.reach <= 0.0:
            raise ValueError("spotlight reach must be positive")
        object.__setattr__(self, "colour", _validate_colour(self.colour))

    def cone_factor(self, to_fragment: Vec3) -> float:
        cos_angle = to_fragment.normalized().dot(-self.direction.normalized())
        inner = math.cos(math.radians(self.inner_degrees))
        outer = math.cos(math.radians(self.outer_degrees))
        if cos_angle <= outer:
            return 0.0
        if cos_angle >= inner:
            return 1.0
        return (cos_angle - outer) / (inner - outer)

    def attenuation(self, distance: float) -> float:
        if distance >= self.reach:
            return 0.0
        return (1.0 - distance / self.reach) ** 2
