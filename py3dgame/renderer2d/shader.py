"""Per-pixel post-processing.

Python pixel shaders trade speed for portability: they are meant for small
frames, offline passes and prototyping the effects a GPU backend will later run
in a fragment shader. Nothing here is a no-op preset - every effect touches
pixels and is covered by tests.
"""

from __future__ import annotations

import math
from typing import Callable

from .canvas import Canvas
from .palette import clamp_channel, luminance, mix

__all__ = [
    "PixelShader",
    "Shader",
    "ShaderStack",
    "grayscale",
    "tint",
    "vignette",
    "scanlines",
    "posterize",
]

PixelShader = Callable[[int, int, tuple], tuple]


class Shader:
    def __init__(self, fn: PixelShader, name: str = "shader") -> None:
        if not callable(fn):
            raise ValueError("a shader needs a callable")
        self.fn = fn
        self.name = name

    def apply(self, canvas: Canvas) -> None:
        for y in range(canvas.height):
            for x in range(canvas.width):
                pixel = canvas.get_pixel(x, y)
                result = self.fn(x, y, pixel)
                if result is None:
                    continue
                r, g, b, a = result
                canvas.set_pixel(x, y, (clamp_channel(r), clamp_channel(g), clamp_channel(b), clamp_channel(a)))


class ShaderStack:
    def __init__(self, *shaders: Shader) -> None:
        self.shaders: list[Shader] = list(shaders)

    def add(self, shader: Shader) -> "ShaderStack":
        if not isinstance(shader, Shader):
            raise ValueError("only Shader instances can be stacked")
        self.shaders.append(shader)
        return self

    def apply(self, canvas: Canvas) -> None:
        for shader in self.shaders:
            shader.apply(canvas)


def grayscale(amount: float = 1.0) -> Shader:
    if not 0.0 <= amount <= 1.0:
        raise ValueError("amount must be within 0..1")

    def fn(x: int, y: int, pixel: tuple) -> tuple:
        r, g, b, a = pixel
        grey = luminance(r, g, b)
        return (r + (grey - r) * amount, g + (grey - g) * amount, b + (grey - b) * amount, a)

    return Shader(fn, "grayscale")


def tint(colour: tuple[int, int, int], strength: float = 1.0) -> Shader:
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be within 0..1")
    target = tuple(colour[:3])

    def fn(x: int, y: int, pixel: tuple) -> tuple:
        r, g, b, a = pixel
        tinted = mix((r, g, b), target, strength * (0.35 + 0.65 * (luminance(r, g, b) / 255)))
        return tinted + (a,)

    return Shader(fn, "tint")


def vignette(strength: float = 0.6) -> Shader:
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be within 0..1")

    def fn(x: int, y: int, pixel: tuple) -> tuple:
        r, g, b, a = pixel
        return (r, g, b, a)

    shader = Shader(fn, "vignette")

    def apply(canvas: Canvas) -> None:
        cx, cy = (canvas.width - 1) / 2, (canvas.height - 1) / 2
        max_d = math.hypot(cx, cy) or 1.0
        for y in range(canvas.height):
            for x in range(canvas.width):
                r, g, b, a = canvas.get_pixel(x, y)
                factor = 1.0 - strength * (math.hypot(x - cx, y - cy) / max_d) ** 2
                canvas.set_pixel(x, y, (
                    clamp_channel(r * factor), clamp_channel(g * factor), clamp_channel(b * factor), a,
                ))

    shader.apply = apply  # type: ignore[assignment]
    return shader


def scanlines(spacing: int = 3, strength: float = 0.25) -> Shader:
    if spacing < 1:
        raise ValueError("spacing must be at least 1")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be within 0..1")

    def fn(x: int, y: int, pixel: tuple) -> tuple:
        r, g, b, a = pixel
        if y % spacing == 0:
            factor = 1.0 - strength
            return (r * factor, g * factor, b * factor, a)
        return pixel

    return Shader(fn, "scanlines")


def posterize(levels: int = 4) -> Shader:
    if levels < 2:
        raise ValueError("levels must be at least 2")
    step = 255 / (levels - 1)

    def fn(x: int, y: int, pixel: tuple) -> tuple:
        r, g, b, a = pixel
        quantise = lambda channel: round(round(channel / step) * step)
        return (quantise(r), quantise(g), quantise(b), a)

    return Shader(fn, "posterize")
