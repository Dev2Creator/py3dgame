"""Shading models for the software backend.

These are honest CPU approximations, not GPU fragment shaders. The PBR path is a
simplified metallic/roughness model with Fresnel and energy conservation; it is
not a reference implementation of a specific BRDF.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

from ..graphics.material import Material
from ..math3d import Vec3
from .light import DirectionalLight, PointLight, SpotLight

Colour = Tuple[float, float, float]


def _srgb(colour: Sequence[int]) -> Colour:
    return (colour[0] / 255.0, colour[1] / 255.0, colour[2] / 255.0)


def _saturate(value: float) -> float:
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value


def _to_byte(value: float) -> int:
    return int(round(_saturate(value) * 255.0))


def sample_colour(material: Material, uv: Tuple[float, float]) -> Colour:
    """Base colour, or the texture colour when one is bound."""
    if material.texture is None:
        return _srgb(material.base_colour)
    u = uv[0] % 1.0
    v = uv[1] % 1.0
    x = min(material.texture.width - 1, int(u * material.texture.width))
    y = min(material.texture.height - 1, int(v * material.texture.height))
    r, g, b, _ = material.texture.get_pixel(x, y)
    return (r / 255.0, g / 255.0, b / 255.0)


def _light_sample(light, world_pos: Vec3):
    """Return (direction to light, attenuation, light colour) or None."""
    if isinstance(light, DirectionalLight):
        return -light.unit_direction, light.intensity, _srgb(light.colour)
    if isinstance(light, PointLight):
        offset = light.position - world_pos
        distance = offset.length()
        if distance <= 1e-6:
            return None
        return offset * (1.0 / distance), light.intensity * light.attenuation(distance), _srgb(light.colour)
    if isinstance(light, SpotLight):
        offset = light.position - world_pos
        distance = offset.length()
        if distance <= 1e-6:
            return None
        factor = light.attenuation(distance) * light.cone_factor(offset)
        if factor <= 0.0:
            return None
        return offset * (1.0 / distance), light.intensity * factor, _srgb(light.colour)
    return None


def shade(material: Material, world_pos: Vec3, normal: Vec3, view_pos: Vec3,
          lights: Iterable, uv: Tuple[float, float] = (0.0, 0.0),
          ambient: Sequence[float] = (0.16, 0.18, 0.22)) -> Tuple[int, int, int, int]:
    base = sample_colour(material, uv)
    emission = _srgb(material.emission)
    n = normal.normalized() if normal.length() > 0.0 else Vec3(0.0, 1.0, 0.0)
    view = (view_pos - world_pos)
    view = view.normalized() if view.length() > 0.0 else Vec3(0.0, 0.0, 1.0)

    if material.shading == "unlit":
        return (_to_byte(base[0] + emission[0]), _to_byte(base[1] + emission[1]),
                _to_byte(base[2] + emission[2]), _to_byte(material.alpha))

    diffuse: Colour = (0.0, 0.0, 0.0)
    specular: Colour = (0.0, 0.0, 0.0)
    shininess = max(2.0, 2.0 ** (1.0 + 9.0 * (1.0 - material.roughness)))

    for light in lights:
        sample = _light_sample(light, world_pos)
        if sample is None:
            continue
        direction, attenuation, colour = sample
        if attenuation <= 0.0:
            continue
        n_dot_l = _saturate(n.dot(direction))
        toon_band = n_dot_l
        if material.shading == "toon":
            toon_band = math.floor(n_dot_l * 3.0 + 0.5) / 3.0
        diffuse = tuple(diffuse[i] + toon_band * attenuation * colour[i] for i in range(3))

        if material.shading in ("phong", "blinn", "toon", "pbr"):
            if material.shading == "blinn":
                half = (direction + view)
                half = half.normalized() if half.length() > 0.0 else view
                spec_angle = _saturate(n.dot(half))
                spec_power = spec_angle ** shininess
            else:
                reflected = n * (2.0 * n.dot(direction)) - direction
                spec_power = _saturate(reflected.dot(view)) ** shininess
            if material.shading == "toon":
                spec_power = 1.0 if spec_power > 0.6 else 0.0
            weight = spec_power * attenuation
            specular = tuple(specular[i] + weight * colour[i] for i in range(3))

    if material.shading == "pbr":
        f0 = 0.04 * (1.0 - material.metallic) + material.metallic
        fresnel = f0 + (1.0 - f0) * ((1.0 - _saturate(n.dot(view))) ** 5)
        diffuse_energy = (1.0 - fresnel) * (1.0 - material.metallic)
        grazing = 0.12 * (1.0 - material.roughness)
        out = []
        for i in range(3):
            value = (base[i] * diffuse[i] * diffuse_energy
                     + specular[i] * fresnel
                     + base[i] * ambient[i] * (1.0 - material.metallic * 0.6)
                     + base[i] * grazing * ambient[i]
                     + emission[i])
            out.append(_to_byte(value))
        return (out[0], out[1], out[2], _to_byte(material.alpha))

    out = []
    for i in range(3):
        value = base[i] * (ambient[i] + diffuse[i]) + specular[i] * (0.25 if material.shading == "toon" else 1.0)
        out.append(_to_byte(value + emission[i]))
    return (out[0], out[1], out[2], _to_byte(material.alpha))
