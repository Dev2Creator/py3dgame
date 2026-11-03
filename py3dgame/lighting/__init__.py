"""3D lights and shading models. The 2D lighting lives in renderer2d."""

from .light import DirectionalLight, PointLight, SpotLight
from .shading import sample_colour, shade

__all__ = ["DirectionalLight", "PointLight", "SpotLight", "sample_colour", "shade"]
