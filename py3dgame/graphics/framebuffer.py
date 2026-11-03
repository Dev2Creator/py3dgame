"""Colour + depth framebuffer for the software backend."""

from __future__ import annotations

import math
from typing import Tuple

from ..renderer2d.image import Image


class ColorBuffer:
    """RGBA colour buffer with a parallel float depth buffer."""

    __slots__ = ("width", "height", "pixels", "depth")

    def __init__(self, width: int, height: int) -> None:
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise ValueError("framebuffer dimensions must be positive")
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 4)
        self.depth = [math.inf] * (width * height)

    def clear(self, colour: Tuple[int, int, int, int] = (10, 12, 18, 255)) -> None:
        r, g, b, a = (max(0, min(255, int(c))) for c in colour)
        self.pixels[:] = bytes((r, g, b, a)) * (self.width * self.height)
        self.depth = [math.inf] * (self.width * self.height)

    def index(self, x: int, y: int) -> int:
        return y * self.width + x

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError("pixel outside the framebuffer")
        i = self.index(x, y) * 4
        p = self.pixels
        return (p[i], p[i + 1], p[i + 2], p[i + 3])

    def set_pixel(self, x: int, y: int, colour: Tuple[int, int, int, int]) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        r, g, b, a = (max(0, min(255, int(c))) for c in colour)
        i = self.index(x, y) * 4
        self.pixels[i:i + 4] = bytes((r, g, b, a))

    def to_image(self) -> Image:
        return Image(self.width, self.height, self.pixels)
