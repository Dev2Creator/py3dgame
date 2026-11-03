"""Vertical mirroring for water, polished floors and glass.

A cheap screen-space mirror: rows above an axis are reflected below it with an
opacity and an optional sine ripple that animates over time.
"""

from __future__ import annotations

import math

from .canvas import Canvas
from .palette import mix

__all__ = ["WaterSurface"]


class WaterSurface:
    def __init__(self, axis_y: int, opacity: float = 0.45, ripple: float = 0.0, speed: float = 1.6) -> None:
        if axis_y <= 0:
            raise ValueError("axis_y must be positive")
        if not 0.0 <= opacity <= 1.0:
            raise ValueError("opacity must be within 0..1")
        if ripple < 0:
            raise ValueError("ripple cannot be negative")
        self.axis_y = int(axis_y)
        self.opacity = float(opacity)
        self.ripple = float(ripple)
        self.speed = float(speed)
        self.phase = 0.0

    def update(self, dt: float) -> float:
        if dt < 0:
            raise ValueError("dt cannot be negative")
        self.phase += dt * self.speed
        return self.phase

    def apply(self, canvas: Canvas) -> None:
        if self.opacity <= 0:
            return
        width, height = canvas.width, canvas.height
        axis = min(self.axis_y, height)
        for source_y in range(min(axis, height)):
            dest_y = axis + (axis - 1 - source_y)
            if dest_y >= height:
                break
            shift = 0
            if self.ripple:
                shift = int(round(self.ripple * math.sin(source_y * 0.45 + self.phase)))
            for x in range(width):
                source_x = (x + shift) % width
                sr, sg, sb, sa = canvas.get_pixel(source_x, source_y)
                dr, dg, db, da = canvas.get_pixel(x, dest_y)
                canvas.set_pixel(x, dest_y, mix((dr, dg, db), (sr, sg, sb), self.opacity) + (da,))
