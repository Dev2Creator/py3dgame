"""Additive 2D lighting into a lightmap, then multiplied over a frame.

This is deliberately the same model a 3D deferred pipeline uses: accumulate
radiance per pixel, then modulate the surface. It is not shadowed yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .canvas import Canvas


@dataclass(frozen=True)
class AmbientLight:
    colour: Tuple[int, int, int] = (255, 255, 255)
    intensity: float = 0.25


@dataclass(frozen=True)
class Light2D:
    position: Tuple[float, float] = (0.0, 0.0)
    radius: float = 64.0
    colour: Tuple[int, int, int] = (255, 255, 255)
    intensity: float = 1.0
    falloff: float = 2.0


class LightMap:
    """Per-pixel RGB radiance in the 0..1 range."""

    __slots__ = ("width", "height", "data")

    def __init__(self, width: int, height: int, data: List[float] | None = None):
        self.width = int(width)
        self.height = int(height)
        self.data = data if data is not None else [0.0] * (self.width * self.height * 3)

    def get(self, x: int, y: int) -> Tuple[float, float, float]:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"lightmap pixel ({x}, {y}) outside bounds")
        i = (y * self.width + x) * 3
        return self.data[i], self.data[i + 1], self.data[i + 2]

    def apply(self, canvas: Canvas) -> None:
        """Multiply the canvas RGB by the lightmap, leaving alpha alone."""
        if canvas.width != self.width or canvas.height != self.height:
            raise ValueError("lightmap and canvas sizes differ")
        surface = canvas.surface
        data = self.data
        for pixel in range(self.width * self.height):
            source = pixel * 3
            target = pixel * 4
            if surface[target + 3] == 0:
                continue
            surface[target] = int(surface[target] * data[source])
            surface[target + 1] = int(surface[target + 1] * data[source + 1])
            surface[target + 2] = int(surface[target + 2] * data[source + 2])


def build_lightmap(
    width: int,
    height: int,
    lights: Sequence[Light2D],
    ambient: AmbientLight | None = None,
) -> LightMap:
    if width <= 0 or height <= 0:
        raise ValueError("lightmap size must be positive")
    ambient = ambient or AmbientLight()
    if not 0.0 <= ambient.intensity:
        raise ValueError("ambient intensity must not be negative")
    base = [ambient.colour[channel] / 255.0 * ambient.intensity for channel in range(3)]
    data = base * (width * height)

    for light in lights:
        if light.radius <= 0:
            raise ValueError("light radius must be positive")
        if light.intensity < 0:
            raise ValueError("light intensity must not be negative")
        red = light.colour[0] / 255.0 * light.intensity
        green = light.colour[1] / 255.0 * light.intensity
        blue = light.colour[2] / 255.0 * light.intensity
        cx, cy = light.position
        radius_sq = light.radius * light.radius
        min_x = max(0, int(cx - light.radius))
        max_x = min(width - 1, int(cx + light.radius))
        min_y = max(0, int(cy - light.radius))
        max_y = min(height - 1, int(cy + light.radius))
        for y in range(min_y, max_y + 1):
            dy = y - cy
            row = y * width
            for x in range(min_x, max_x + 1):
                dx = x - cx
                distance_sq = dx * dx + dy * dy
                if distance_sq > radius_sq:
                    continue
                attenuation = (1.0 - (distance_sq ** 0.5) / light.radius) ** light.falloff
                if attenuation <= 0.0:
                    continue
                i = (row + x) * 3
                data[i] = min(1.0, data[i] + red * attenuation)
                data[i + 1] = min(1.0, data[i + 1] + green * attenuation)
                data[i + 2] = min(1.0, data[i + 2] + blue * attenuation)
    return LightMap(width, height, data)
