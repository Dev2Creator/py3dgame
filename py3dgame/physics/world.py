"""Fixed-timestep physics world: integration, contacts, impulses, raycasts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from ..math3d import Vec2
from .body import Body, Box, Circle
from .collision import collide

POSITION_SLOP = 0.02
CORRECTION_FACTOR = 1.0
RESTING_SPEED = 1.0
BOUNCE_THRESHOLD = 30.0


@dataclass(frozen=True)
class Contact:
    a: Body
    b: Body
    normal: Vec2
    penetration: float
    is_trigger: bool


@dataclass(frozen=True)
class RayHit:
    body: Body
    point: Vec2
    distance: float
    normal: Vec2


class PhysicsWorld:
    def __init__(
        self,
        gravity: Tuple[float, float] = (0.0, 900.0),
        fixed_dt: float = 1.0 / 60.0,
        iterations: int = 4,
    ):
        if fixed_dt <= 0:
            raise ValueError("fixed_dt must be positive")
        if iterations < 1:
            raise ValueError("iterations must be at least 1")
        self.gravity = Vec2(*gravity)
        self.fixed_dt = float(fixed_dt)
        self.iterations = int(iterations)
        self.bodies: List[Body] = []
        self.contacts: List[Contact] = []
        self.time = 0.0

    # -- scene management ----------------------------------------------
    def add(self, body: Body) -> Body:
        if body in self.bodies:
            return body
        self.bodies.append(body)
        return body

    def remove(self, body: Body) -> bool:
        if body in self.bodies:
            self.bodies.remove(body)
            return True
        return False

    def clear(self) -> None:
        self.bodies.clear()
        self.contacts.clear()
        self.time = 0.0

    # -- simulation -----------------------------------------------------
    def step(self, dt: float | None = None) -> List[Contact]:
        step_dt = self.fixed_dt if dt is None else float(dt)
        if step_dt <= 0:
            raise ValueError("dt must be positive")

        for body in self.bodies:
            if body.static:
                body.force = Vec2(0.0, 0.0)
                continue
            body.previous_position = Vec2(body.position.x, body.position.y)
            acceleration = self.gravity * body.gravity_scale + body.force * body.inv_mass
            body.velocity = body.velocity + acceleration * step_dt
            if body.linear_damping:
                body.velocity = body.velocity * max(0.0, 1.0 - body.linear_damping * step_dt)
            body.position = body.position + body.velocity * step_dt
            body.force = Vec2(0.0, 0.0)

        # Continuous phase: a fast body whose step displacement is larger than
        # its own size could otherwise pass straight through a thin platform.
        for body in self.bodies:
            if not body.static:
                self._continuous_check(body, step_dt)

        contacts = self._detect()
        # Positional correction happens once per contact: applying it inside the
        # impulse loop would eject bodies by iterations * penetration.
        for contact in contacts:
            if not contact.is_trigger:
                self._correct_positions(contact)
        for _ in range(self.iterations):
            for contact in contacts:
                if not contact.is_trigger:
                    self._resolve(contact)

        self.contacts = contacts
        self.time += step_dt
        return contacts

    def _continuous_check(self, body: Body, dt: float) -> None:
        if body.previous_position is None:
            return
        displacement = body.position - body.previous_position
        distance = displacement.length()
        if distance <= 0.0:
            return
        half_x, half_y = body.shape.half_extents()
        if distance <= min(half_x, half_y):
            return
        hit = self._raycast(body.previous_position, displacement, distance, ignore=body)
        if hit is None:
            return
        unit = displacement * (1.0 / distance)
        if isinstance(body.shape, Circle):
            extent = body.shape.radius
        else:
            extent = abs(unit.x) * body.shape.half_width + abs(unit.y) * body.shape.half_height
        body.position = hit.point - unit * (extent + 1e-3)

        closing = body.velocity.dot(hit.normal)
        if closing < 0.0:
            restitution = body.restitution if -closing > BOUNCE_THRESHOLD else 0.0
            body.velocity = body.velocity - hit.normal * (closing * (1.0 + restitution))

    def _raycast(
        self,
        origin: Vec2,
        direction: Vec2,
        max_distance: float,
        ignore: Body | None = None,
    ) -> Optional[RayHit]:
        length = direction.length()
        if length < 1e-9:
            return None
        unit = direction * (1.0 / length)
        best: Optional[RayHit] = None
        for body in self.bodies:
            if body is ignore:
                continue
            hit = self._ray_body(origin, unit, max_distance, body)
            if hit is None:
                continue
            if best is None or hit.distance < best.distance:
                best = hit
        return best

    def _should_test(self, a: Body, b: Body) -> bool:
        if a.static and b.static:
            return False
        return bool(a.layer & b.mask) and bool(b.layer & a.mask)

    def _detect(self) -> List[Contact]:
        ordered = sorted(self.bodies, key=lambda body: body.aabb()[0])
        found: List[Contact] = []
        for index, a in enumerate(ordered):
            max_x = a.aabb()[2]
            for other in ordered[index + 1:]:
                if other.aabb()[0] > max_x:
                    break
                if not self._should_test(a, other):
                    continue
                manifold = collide(a, other)
                if manifold is None:
                    continue
                found.append(
                    Contact(
                        a=a,
                        b=other,
                        normal=manifold.normal,
                        penetration=manifold.penetration,
                        is_trigger=a.is_trigger or other.is_trigger,
                    )
                )
        return found

    def _correct_positions(self, contact: Contact) -> None:
        a, b = contact.a, contact.b
        inverse_mass = a.inv_mass + b.inv_mass
        if inverse_mass == 0.0:
            return
        normal = contact.normal
        correction = max(contact.penetration - POSITION_SLOP, 0.0) / inverse_mass
        if correction:
            a.position = a.position - normal * (correction * a.inv_mass * CORRECTION_FACTOR)
            b.position = b.position + normal * (correction * b.inv_mass * CORRECTION_FACTOR)

    def _resolve(self, contact: Contact) -> None:
        a, b = contact.a, contact.b
        inverse_mass = a.inv_mass + b.inv_mass
        if inverse_mass == 0.0:
            return

        normal = contact.normal
        relative = b.velocity - a.velocity
        separating = relative.dot(normal)
        if separating > 0:
            return

        resting = separating > -RESTING_SPEED
        restitution = max(a.restitution, b.restitution) if -separating > BOUNCE_THRESHOLD else 0.0
        impulse = -(1.0 + restitution) * separating / inverse_mass
        a.velocity = a.velocity - normal * (impulse * a.inv_mass)
        b.velocity = b.velocity + normal * (impulse * b.inv_mass)

        tangent_velocity = relative - normal * separating
        if tangent_velocity.length_squared() > 1e-12:
            tangent = tangent_velocity.normalized()
            friction_impulse = -relative.dot(tangent) / inverse_mass
            mu = (a.friction + b.friction) * 0.5
            limit = abs(impulse) * mu
            friction_impulse = max(-limit, min(limit, friction_impulse))
            a.velocity = a.velocity - tangent * (friction_impulse * a.inv_mass)
            b.velocity = b.velocity + tangent * (friction_impulse * b.inv_mass)

        if resting:
            # Kill the leftover normal velocity so a body at rest does not
            # jitter between "falling" and "ejected" every frame.
            residual = (b.velocity - a.velocity).dot(normal)
            if residual:
                a.velocity = a.velocity + normal * (residual * a.inv_mass / inverse_mass)
                b.velocity = b.velocity - normal * (residual * b.inv_mass / inverse_mass)

    # -- queries ---------------------------------------------------------
    def overlap(self, point: Vec2) -> List[Body]:
        return [body for body in self.bodies if body.contains_point(point)]

    def raycast(
        self,
        origin: Vec2,
        direction: Vec2,
        max_distance: float = 1000.0,
    ) -> Optional[RayHit]:
        if max_distance <= 0:
            raise ValueError("max_distance must be positive")
        length = direction.length()
        if length < 1e-9:
            raise ValueError("ray direction must not be zero")
        unit = direction * (1.0 / length)

        return self._raycast(origin, direction, max_distance)

    def _ray_body(self, origin: Vec2, unit: Vec2, max_distance: float, body: Body) -> Optional[RayHit]:
        if isinstance(body.shape, Circle):
            return _ray_circle(origin, unit, max_distance, body)
        return _ray_box(origin, unit, max_distance, body)


def _ray_circle(origin: Vec2, unit: Vec2, max_distance: float, body: Body) -> Optional[RayHit]:
    radius = body.shape.radius  # type: ignore[union-attr]
    offset = origin - body.position
    b = offset.dot(unit)
    c = offset.length_squared() - radius * radius
    discriminant = b * b - c
    if discriminant < 0:
        return None
    root = discriminant ** 0.5
    distance = -b - root
    if distance < 0:
        distance = -b + root
    if distance < 0 or distance > max_distance:
        return None
    point = origin + unit * distance
    normal = (point - body.position).normalized()
    return RayHit(body, point, distance, normal)


def _ray_box(origin: Vec2, unit: Vec2, max_distance: float, body: Body) -> Optional[RayHit]:
    half_width = body.shape.half_width  # type: ignore[union-attr]
    half_height = body.shape.half_height  # type: ignore[union-attr]
    min_x, min_y = body.position.x - half_width, body.position.y - half_height
    max_x, max_y = body.position.x + half_width, body.position.y + half_height

    t_min, t_max = 0.0, max_distance
    normal = Vec2(0.0, 0.0)
    for axis_origin, axis_direction, lower, upper, axis in (
        (origin.x, unit.x, min_x, max_x, 0),
        (origin.y, unit.y, min_y, max_y, 1),
    ):
        if abs(axis_direction) < 1e-12:
            if axis_origin < lower or axis_origin > upper:
                return None
            continue
        inverse = 1.0 / axis_direction
        t1 = (lower - axis_origin) * inverse
        t2 = (upper - axis_origin) * inverse
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > t_min:
            t_min = t1
            if axis == 0:
                normal = Vec2(-1.0 if axis_direction > 0 else 1.0, 0.0)
            else:
                normal = Vec2(0.0, -1.0 if axis_direction > 0 else 1.0)
        if t2 < t_max:
            t_max = t2
        if t_min > t_max:
            return None
    if t_min > max_distance:
        return None
    point = origin + unit * t_min
    return RayHit(body, point, t_min, normal)
