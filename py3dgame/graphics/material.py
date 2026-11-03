"""Material description shared by every shading model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..renderer2d.image import Image

SHADING_MODELS = ("unlit", "lambert", "phong", "blinn", "toon", "pbr")


@dataclass
class Material:
    base_colour: Tuple[int, int, int] = (214, 216, 224)
    metallic: float = 0.0
    roughness: float = 0.55
    emission: Tuple[int, int, int] = (0, 0, 0)
    alpha: float = 1.0
    shading: str = "lambert"
    texture: Optional[Image] = None
    double_sided: bool = False

    def __post_init__(self) -> None:
        if self.shading not in SHADING_MODELS:
            raise ValueError(f"unknown shading model {self.shading!r}; expected one of {SHADING_MODELS}")
        if not 0.0 <= self.metallic <= 1.0:
            raise ValueError("metallic must be between 0 and 1")
        if not 0.0 <= self.roughness <= 1.0:
            raise ValueError("roughness must be between 0 and 1")
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        for name in ("base_colour", "emission"):
            value = getattr(self, name)
            if len(value) != 3 or any(not 0 <= int(c) <= 255 for c in value):
                raise ValueError(f"{name} must be three channels between 0 and 255")
