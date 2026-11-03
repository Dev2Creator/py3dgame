"""Small colour helpers shared by the atmosphere passes."""

from __future__ import annotations

Colour = tuple
RGBA = tuple


def clamp_channel(value: float) -> int:
    return 0 if value <= 0 else 255 if value >= 255 else int(round(value))


def mix(a, b, t: float):
    """Linear interpolation between two RGB(A) tuples; t is clamped to 0..1."""
    t = 0.0 if t <= 0 else 1.0 if t >= 1 else t
    size = min(len(a), len(b))
    return tuple(clamp_channel(a[i] + (b[i] - a[i]) * t) for i in range(size))


def scale(colour, factor: float):
    return tuple(clamp_channel(channel * factor) for channel in colour)


def luminance(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
