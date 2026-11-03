"""Narrow-phase collision detection for circles and axis-aligned boxes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..math3d import Vec2
from .body import Body, Box, Circle


@dataclass(frozen=True)
class Manifold:
    normal: Vec2      # unit vector pointing from a towards b
    penetration: float
    contact: Vec2


def _circle_circle(a: Body, b: Body) -> Optional[Manifold]:
    delta = b.position - a.position
    radius = a.shape.radius + b.shape.radius  # type: ignore[union-attr]
    distance_sq = delta.length_squared()
    if distance_sq > radius * radius:
        return None
    distance = distance_sq ** 0.5
    if distance < 1e-9:
        normal = Vec2(1.0, 0.0)
        contact = a.position
    else:
        normal = delta * (1.0 / distance)
        contact = a.position + normal * a.shape.radius  # type: ignore[union-attr]
    return Manifold(normal, radius - distance, contact)


def _circle_box(circle_body: Body, box_body: Body) -> Optional[Manifold]:
    radius = circle_body.shape.radius  # type: ignore[union-attr]
    half_width = box_body.shape.half_width  # type: ignore[union-attr]
    half_height = box_body.shape.half_height  # type: ignore[union-attr]
    centre = circle_body.position
    box_centre = box_body.position

    closest = Vec2(
        max(box_centre.x - half_width, min(centre.x, box_centre.x + half_width)),
        max(box_centre.y - half_height, min(centre.y, box_centre.y + half_height)),
    )
    delta = closest - centre
    distance_sq = delta.length_squared()
    if distance_sq > radius * radius:
        return None
    if distance_sq > 1e-12:
        distance = distance_sq ** 0.5
        normal = delta * (1.0 / distance)
        return Manifold(normal, radius - distance, closest)

    # Centre is inside the box: exit through the nearest face. The manifold
    # normal still points from the circle towards the box, so it is opposite
    # the exit direction.
    left = centre.x - (box_centre.x - half_width)
    right = (box_centre.x + half_width) - centre.x
    top = centre.y - (box_centre.y - half_height)
    bottom = (box_centre.y + half_height) - centre.y

    # Exit through the face the body came from. A fast body can end a step deep
    # inside a thin platform; nearest-face alone would then push it out of the
    # far side and tunnel it straight through the floor.
    previous = circle_body.previous_position
    if previous is not None and previous.y <= box_centre.y - half_height:
        exit_normal, thickness = Vec2(0.0, -1.0), top
    elif previous is not None and previous.y >= box_centre.y + half_height:
        exit_normal, thickness = Vec2(0.0, 1.0), bottom
    elif previous is not None and previous.x <= box_centre.x - half_width:
        exit_normal, thickness = Vec2(-1.0, 0.0), left
    elif previous is not None and previous.x >= box_centre.x + half_width:
        exit_normal, thickness = Vec2(1.0, 0.0), right
    else:
        smallest = min(left, right, top, bottom)
        if smallest == left:
            exit_normal = Vec2(-1.0, 0.0)
        elif smallest == right:
            exit_normal = Vec2(1.0, 0.0)
        elif smallest == top:
            exit_normal = Vec2(0.0, -1.0)
        else:
            exit_normal = Vec2(0.0, 1.0)
        thickness = smallest

    return Manifold(exit_normal * -1.0, radius + thickness, closest)


def _box_box(a: Body, b: Body) -> Optional[Manifold]:
    width_a = a.shape.half_width  # type: ignore[union-attr]
    height_a = a.shape.half_height  # type: ignore[union-attr]
    width_b = b.shape.half_width  # type: ignore[union-attr]
    height_b = b.shape.half_height  # type: ignore[union-attr]

    delta = b.position - a.position
    overlap_x = (width_a + width_b) - abs(delta.x)
    if overlap_x <= 0:
        return None
    overlap_y = (height_a + height_b) - abs(delta.y)
    if overlap_y <= 0:
        return None

    if overlap_x < overlap_y:
        normal = Vec2(1.0 if delta.x >= 0 else -1.0, 0.0)
        penetration = overlap_x
    else:
        normal = Vec2(0.0, 1.0 if delta.y >= 0 else -1.0)
        penetration = overlap_y

    contact = Vec2(
        (a.position.x + b.position.x) * 0.5,
        (a.position.y + b.position.y) * 0.5,
    )
    return Manifold(normal, penetration, contact)


def collide(a: Body, b: Body) -> Optional[Manifold]:
    """Return the contact manifold with a normal pointing from a to b."""
    a_circle = isinstance(a.shape, Circle)
    b_circle = isinstance(b.shape, Circle)

    if a_circle and b_circle:
        return _circle_circle(a, b)
    if a_circle and isinstance(b.shape, Box):
        return _circle_box(a, b)
    if isinstance(a.shape, Box) and b_circle:
        manifold = _circle_box(b, a)
        if manifold is None:
            return None
        return Manifold(manifold.normal * -1.0, manifold.penetration, manifold.contact)
    if isinstance(a.shape, Box) and isinstance(b.shape, Box):
        return _box_box(a, b)
    raise TypeError("unsupported shape combination")
