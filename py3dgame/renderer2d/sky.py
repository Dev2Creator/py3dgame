"""Procedural sky: vertical gradient, horizon haze, sun disc and stars.

The palette comes from the day/night clock, so a sky drawn every frame follows
the same sun that lights the world.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from ..world.daynight import SunState
from .canvas import Canvas
from .palette import mix, scale

__all__ = ["Sky", "SkySettings"]


@dataclass(frozen=True)
class SkySettings:
    haze_height: float = 0.55
    haze_strength: float = 0.45
    sun_radius: float = 6.0
    star_count: int = 48
    seed: int = 7

    def __post_init__(self) -> None:
        if not 0.0 <= self.haze_height <= 1.0:
            raise ValueError("haze_height must be within 0..1")
        if not 0.0 <= self.haze_strength <= 1.0:
            raise ValueError("haze_strength must be within 0..1")
        if self.sun_radius <= 0:
            raise ValueError("sun_radius must be positive")
        if self.star_count < 0:
            raise ValueError("star_count cannot be negative")


class Sky:
    def __init__(self, settings: SkySettings | None = None) -> None:
        self.settings = settings or SkySettings()

    def draw(self, canvas: Canvas, state: SunState, sun_x: float = 0.5) -> None:
        width, height = canvas.width, canvas.height
        top = state.sky_colour
        horizon = mix(state.sky_colour, state.sun_colour, 0.35 * state.sun_intensity)
        haze_colour = mix(horizon, (226, 230, 236), 0.5)

        for y in range(height):
            t = y / max(1, height - 1)
            row = mix(top, horizon, t ** 1.25)
            band = 1.0 - abs(t - self.settings.haze_height) / max(self.settings.haze_height, 1e-6)
            if band > 0.0:
                row = mix(row, haze_colour, band * self.settings.haze_strength)
            canvas.fill_rect(0, y, width, 1, row + (255,))

        self._draw_stars(canvas, state)
        self._draw_sun(canvas, state, sun_x)

    def _draw_stars(self, canvas: Canvas, state: SunState) -> None:
        visible = 1.0 - min(1.0, state.sun_intensity / 0.25)
        if visible <= 0.0 or self.settings.star_count == 0:
            return
        rng = random.Random(self.settings.seed)
        for _ in range(self.settings.star_count):
            x = rng.randrange(canvas.width)
            y = rng.randrange(max(1, int(canvas.height * 0.6)))
            brightness = rng.uniform(0.35, 1.0) * visible
            colour = scale((214, 224, 255), brightness)
            canvas.set_pixel(x, y, colour + (255,))

    def _draw_sun(self, canvas: Canvas, state: SunState, sun_x: float) -> None:
        if state.elevation <= -4.0:
            return
        horizon_y = canvas.height * 0.62
        lift = math.sin(math.radians(max(-10.0, state.elevation))) * canvas.height * 0.42
        cx = sun_x * canvas.width
        cy = horizon_y - lift
        radius = self.settings.sun_radius * (0.7 + 0.5 * state.sun_intensity)
        canvas.draw_circle(cx, cy, radius, state.sun_colour + (255,))
