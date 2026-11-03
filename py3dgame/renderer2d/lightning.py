"""Transient lightning: flash envelope, screen glow and a jagged bolt."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .canvas import Canvas
from .palette import clamp_channel

__all__ = ["Lightning"]


@dataclass
class _Flash:
    intensity: float
    duration: float
    age: float = 0.0


class Lightning:
    def __init__(self, colour: tuple[int, int, int] = (214, 228, 255), seed: int = 11) -> None:
        self.colour = colour
        self._flashes: list[_Flash] = []
        self._rng = random.Random(seed)
        self.strikes = 0

    def trigger(self, intensity: float = 1.0, duration: float = 0.22) -> None:
        if not 0.0 < intensity <= 1.0:
            raise ValueError("intensity must be within 0..1")
        if duration <= 0:
            raise ValueError("duration must be positive")
        self._flashes.append(_Flash(intensity, duration))
        self.strikes += 1

    def update(self, dt: float) -> float:
        if dt < 0:
            raise ValueError("dt cannot be negative")
        for flash in self._flashes:
            flash.age += dt
        self._flashes = [f for f in self._flashes if f.age < f.duration]
        return self.level()

    def level(self) -> float:
        if not self._flashes:
            return 0.0
        return min(1.0, max(f.intensity * (1.0 - f.age / f.duration) ** 2 for f in self._flashes))

    def draw(self, canvas: Canvas, level: float | None = None) -> None:
        glow = self.level() if level is None else max(0.0, min(1.0, level))
        if glow <= 0.0:
            return
        add = [channel * glow * 0.8 for channel in self.colour]
        for y in range(canvas.height):
            for x in range(canvas.width):
                r, g, b, a = canvas.get_pixel(x, y)
                canvas.set_pixel(x, y, (
                    clamp_channel(r + add[0]),
                    clamp_channel(g + add[1]),
                    clamp_channel(b + add[2]),
                    a,
                ))

    def draw_bolt(self, canvas: Canvas, x_end: float, level: float | None = None, segments: int = 8) -> None:
        glow = self.level() if level is None else max(0.0, min(1.0, level))
        if glow <= 0.0 or segments < 1:
            return
        colour = tuple(clamp_channel(c * (0.6 + 0.4 * glow)) for c in self.colour) + (255,)
        x = canvas.width * 0.5
        y = 0.0
        step_y = (canvas.height * 0.75) / segments
        for index in range(1, segments + 1):
            next_x = x_end if index == segments else x + self._rng.uniform(-canvas.width * 0.12, canvas.width * 0.12)
            next_y = step_y * index
            canvas.draw_line(x, y, next_x, next_y, colour)
            x, y = next_x, next_y
