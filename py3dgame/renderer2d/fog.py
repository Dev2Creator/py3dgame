"""Depth-cued fog for 2D frames.

Fog is expressed as a density and a falloff curve so the same parameters can be
handed to a future 3D pipeline instead of being baked into a backdrop image.
"""

from __future__ import annotations

from dataclasses import dataclass

from .canvas import Canvas
from .palette import mix

__all__ = ["Fog", "FogSettings"]


@dataclass(frozen=True)
class FogSettings:
    colour: tuple[int, int, int] = (198, 206, 214)
    density: float = 0.45
    horizon: float = 0.6
    falloff: float = 2.2

    def __post_init__(self) -> None:
        if not 0.0 <= self.density <= 1.0:
            raise ValueError("fog density must be within 0..1")
        if not 0.0 <= self.horizon < 1.0:
            raise ValueError("fog horizon must be within 0..1")
        if self.falloff <= 0:
            raise ValueError("fog falloff must be positive")


class Fog:
    def __init__(self, settings: FogSettings | None = None) -> None:
        self.settings = settings or FogSettings()

    def blend(self, depth: float) -> float:
        """Fog factor for a normalised depth of 0 (near) to 1 (far)."""
        depth = 0.0 if depth <= 0 else 1.0 if depth >= 1 else depth
        return self.settings.density * (depth ** self.settings.falloff)

    def apply(self, canvas: Canvas) -> None:
        if self.settings.density <= 0:
            return
        height = canvas.height
        span = max(1e-6, 1.0 - self.settings.horizon)
        colour = self.settings.colour
        for y in range(height):
            depth = (y / max(1, height - 1) - self.settings.horizon) / span
            factor = self.blend(depth)
            if factor <= 0:
                continue
            for x in range(canvas.width):
                r, g, b, a = canvas.get_pixel(x, y)
                canvas.set_pixel(x, y, mix((r, g, b), colour, factor) + (a,))
