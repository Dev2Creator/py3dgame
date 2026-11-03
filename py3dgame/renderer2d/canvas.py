"""Software 2D rasteriser.

Writes straight into an RGBA byte buffer so the same output feeds the headless
window, PNG export and (via ``Window.present``) any real backend. Primitives are
clipped to the canvas; drawing outside the frame is ignored rather than raising,
which is what gameplay code expects.
"""

from __future__ import annotations

from typing import Sequence, Tuple

__all__ = ["Canvas", "Color"]

Color = Sequence[int]


def _rgba(color: Color) -> Tuple[int, int, int, int]:
    if len(color) == 3:
        r, g, b = color
        a = 255
    elif len(color) == 4:
        r, g, b, a = color
    else:
        raise ValueError("colour must have 3 or 4 components")
    values = (int(r), int(g), int(b), int(a))
    if any(v < 0 or v > 255 for v in values):
        raise ValueError("colour components must be in 0..255")
    return values


class Canvas:
    """An RGBA framebuffer with primitive drawing operations."""

    __slots__ = ("width", "height", "surface")

    def __init__(self, width: int, height: int) -> None:
        if int(width) <= 0 or int(height) <= 0:
            raise ValueError("canvas width and height must be positive")
        self.width = int(width)
        self.height = int(height)
        self.surface = bytearray(self.width * self.height * 4)

    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)

    def resize(self, width: int, height: int) -> None:
        if int(width) <= 0 or int(height) <= 0:
            raise ValueError("canvas width and height must be positive")
        self.width, self.height = int(width), int(height)
        self.surface = bytearray(self.width * self.height * 4)

    def clear(self, color: Color = (0, 0, 0, 255)) -> None:
        self.surface[:] = bytes(_rgba(color)) * (self.width * self.height)

    def set_pixel(self, x: int, y: int, color: Color) -> None:
        x, y = int(x), int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            r, g, b, a = _rgba(color)
            offset = (y * self.width + x) * 4
            self.surface[offset:offset + 4] = bytes((r, g, b, a))

    def blend_pixel(self, x: int, y: int, colour) -> None:
        """Alpha-blend a colour over the canvas, clipping at the edges."""
        r, g, b, a = _rgba(colour)
        if a == 0:
            return
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        i = (y * self.width + x) * 4
        buffer = self.surface
        if a == 255:
            buffer[i:i + 4] = bytes((r, g, b, 255))
            return
        inv = 255 - a
        buffer[i] = (r * a + buffer[i] * inv) // 255
        buffer[i + 1] = (g * a + buffer[i + 1] * inv) // 255
        buffer[i + 2] = (b * a + buffer[i + 2] * inv) // 255
        buffer[i + 3] = min(255, buffer[i + 3] + a)

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        x, y = int(x), int(y)
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"pixel ({x}, {y}) is outside the {self.width}x{self.height} canvas")
        offset = (y * self.width + x) * 4
        return tuple(self.surface[offset:offset + 4])  # type: ignore[return-value]

    def fill_rect(self, x: int, y: int, width: int, height: int, color: Color) -> None:
        rgba = _rgba(color)
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.width, int(x) + int(width))
        y1 = min(self.height, int(y) + int(height))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(rgba) * (x1 - x0)
        stride = self.width * 4
        start = x0 * 4
        for row_index in range(y0, y1):
            offset = row_index * stride + start
            self.surface[offset:offset + len(row)] = row

    def draw_rect(self, x: int, y: int, width: int, height: int, color: Color,
                  thickness: int = 1) -> None:
        t = max(1, int(thickness))
        self.fill_rect(x, y, width, t, color)
        self.fill_rect(x, y + int(height) - t, width, t, color)
        self.fill_rect(x, y, t, height, color)
        self.fill_rect(x + int(width) - t, y, t, height, color)

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            err2 = 2 * err
            if err2 >= dy:
                err += dy
                x0 += sx
            if err2 <= dx:
                err += dx
                y0 += sy

    def draw_circle(self, cx: int, cy: int, radius: int, color: Color,
                    filled: bool = True) -> None:
        cx, cy, r = int(cx), int(cy), int(radius)
        if r < 0:
            raise ValueError("radius must not be negative")
        if r == 0:
            self.set_pixel(cx, cy, color)
            return
        x, y, err = r, 0, 0
        while x >= y:
            if filled:
                self.fill_rect(cx - x, cy + y, 2 * x + 1, 1, color)
                self.fill_rect(cx - x, cy - y, 2 * x + 1, 1, color)
                self.fill_rect(cx - y, cy + x, 2 * y + 1, 1, color)
                self.fill_rect(cx - y, cy - x, 2 * y + 1, 1, color)
            else:
                for px, py in ((x, y), (y, x), (-y, x), (-x, y),
                               (-x, -y), (-y, -x), (y, -x), (x, -y)):
                    self.set_pixel(cx + px, cy + py, color)
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x

    def to_rgb_rows(self) -> list:
        """Debug helper: rows of (r, g, b) tuples, useful in tests and snapshots."""
        rows = []
        for y in range(self.height):
            base = y * self.width * 4
            rows.append([
                tuple(self.surface[base + x * 4:base + x * 4 + 3])
                for x in range(self.width)
            ])
        return rows

    def __repr__(self) -> str:
        return f"Canvas({self.width}x{self.height})"
