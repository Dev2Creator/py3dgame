"""Sprites, sprite sheets and frame animation."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from ..exceptions import ConfigurationError
from .canvas import Canvas
from .image import Image


def _rgba(colour: Iterable[int]) -> Tuple[int, int, int, int]:
    values = tuple(colour)
    if len(values) == 3:
        values = values + (255,)
    if len(values) != 4 or any(not isinstance(v, int) or not 0 <= v <= 255 for v in values):
        raise ValueError("tint must be three or four integers in 0..255")
    return values  # type: ignore[return-value]


class Sprite:
    """A drawable image with position, scaling, tint and opacity."""

    def __init__(
        self,
        image: Image,
        position: Tuple[float, float] = (0.0, 0.0),
        size: Tuple[float, float] | None = None,
        anchor: Tuple[float, float] = (0.0, 0.0),
        tint: Tuple[int, ...] = (255, 255, 255, 255),
        opacity: float = 1.0,
        flip_x: bool = False,
        flip_y: bool = False,
        visible: bool = True,
    ):
        if not isinstance(image, Image):
            raise ConfigurationError("Sprite needs an Image")
        if not 0.0 <= opacity <= 1.0:
            raise ValueError("opacity must be within 0..1")
        self.image = image
        self.position = (float(position[0]), float(position[1]))
        self.size = None if size is None else (float(size[0]), float(size[1]))
        self.anchor = (float(anchor[0]), float(anchor[1]))
        self.tint = _rgba(tint)
        self.opacity = float(opacity)
        self.flip_x = flip_x
        self.flip_y = flip_y
        self.visible = visible

    def draw_size(self) -> Tuple[int, int]:
        width, height = self.size if self.size else self.image.size()
        return max(0, int(round(width))), max(0, int(round(height)))

    def draw(self, canvas: Canvas) -> None:
        if not self.visible or self.opacity <= 0.0:
            return
        target_w, target_h = self.draw_size()
        if target_w == 0 or target_h == 0:
            return
        source = self.image
        left = int(round(self.position[0] - self.anchor[0] * target_w))
        top = int(round(self.position[1] - self.anchor[1] * target_h))
        tr, tg, tb, ta = self.tint
        alpha_scale = self.opacity * (ta / 255.0)
        for dy in range(target_h):
            sy = int(dy * source.height / target_h)
            if self.flip_y:
                sy = source.height - 1 - sy
            for dx in range(target_w):
                sx = int(dx * source.width / target_w)
                if self.flip_x:
                    sx = source.width - 1 - sx
                r, g, b, a = source.pixels[((sy * source.width) + sx) * 4:((sy * source.width) + sx) * 4 + 4]
                if a == 0:
                    continue
                alpha = (a / 255.0) * alpha_scale
                if alpha <= 0.0:
                    continue
                canvas.blend_pixel(
                    left + dx,
                    top + dy,
                    (r * tr // 255, g * tg // 255, b * tb // 255, int(round(alpha * 255))),
                )


class SpriteSheet:
    """A grid of equally sized frames inside one image."""

    def __init__(self, image: Image, frame_width: int, frame_height: int):
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("frame size must be positive")
        if frame_width > image.width or frame_height > image.height:
            raise ValueError("frame size exceeds the sheet image")
        self.image = image
        self.frame_width = int(frame_width)
        self.frame_height = int(frame_height)
        self.columns = image.width // self.frame_width
        self.rows = image.height // self.frame_height
        if self.columns == 0 or self.rows == 0:
            raise ValueError("sheet contains no complete frames")

    @property
    def frame_count(self) -> int:
        return self.columns * self.rows

    def frame(self, index: int) -> Image:
        if not 0 <= index < self.frame_count:
            raise IndexError(f"frame {index} outside 0..{self.frame_count - 1}")
        column = index % self.columns
        row = index // self.columns
        return self.image.crop(
            column * self.frame_width,
            row * self.frame_height,
            self.frame_width,
            self.frame_height,
        )

    def sprite(self, index: int, **kwargs) -> Sprite:
        return Sprite(self.frame(index), **kwargs)


class Animation:
    """A timed sequence of frames."""

    def __init__(
        self,
        frames: Sequence[Image],
        durations: float | Sequence[float] = 0.1,
        loop: bool = True,
        name: str = "",
    ):
        if not frames:
            raise ValueError("an animation needs at least one frame")
        if isinstance(durations, (int, float)):
            durations = [float(durations)] * len(frames)
        if len(durations) != len(frames):
            raise ValueError("durations must match the number of frames")
        if any(d <= 0 for d in durations):
            raise ValueError("frame durations must be positive")
        self.frames: List[Image] = list(frames)
        self.durations = [float(d) for d in durations]
        self.loop = loop
        self.name = name
        self.index = 0
        self.elapsed = 0.0
        self.finished = False

    @classmethod
    def from_sheet(cls, sheet: SpriteSheet, **kwargs) -> "Animation":
        return cls([sheet.frame(i) for i in range(sheet.frame_count)], **kwargs)

    def current(self) -> Image:
        return self.frames[self.index]

    def reset(self) -> None:
        self.index = 0
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt: float) -> Image:
        if dt < 0:
            raise ValueError("dt must not be negative")
        if self.finished and not self.loop:
            return self.current()
        self.elapsed += dt
        while self.elapsed >= self.durations[self.index]:
            self.elapsed -= self.durations[self.index]
            if self.index + 1 < len(self.frames):
                self.index += 1
            elif self.loop:
                self.index = 0
            else:
                self.finished = True
                self.elapsed = 0.0
                break
        return self.current()


class AnimatedSprite(Sprite):
    """A sprite driven by an Animation."""

    def __init__(self, animation: Animation, **kwargs):
        self.animation = animation
        super().__init__(animation.current(), **kwargs)

    def update(self, dt: float) -> None:
        self.image = self.animation.update(dt)
