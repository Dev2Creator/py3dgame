"""Rigid-body physics: integration, contacts, filtering, queries."""

from __future__ import annotations

import pytest

import py3dgame as p3d
from py3dgame.math3d import Vec2


def world_with_ground(**kwargs):
    world = p3d.PhysicsWorld(gravity=(0.0, 900.0), **kwargs)
    ground = world.add(p3d.Body(p3d.Box(50, 1), Vec2(0, 10), static=True, name="ground"))
    return world, ground


def test_body_validation():
    with pytest.raises(ValueError):
        p3d.Body(p3d.Circle(1), mass=0)
    with pytest.raises(ValueError):
        p3d.Body(p3d.Circle(1), restitution=1.5)
    with pytest.raises(ValueError):
        p3d.Body(p3d.Box(0, 1))


def test_collision_normals_point_from_a_to_b():
    a = p3d.Body(p3d.Circle(1), Vec2(0, 0))
    b = p3d.Body(p3d.Circle(1), Vec2(1.5, 0))
    manifold = p3d.collide(a, b)
    assert manifold is not None
    assert manifold.normal.x == pytest.approx(1.0)
    assert manifold.penetration == pytest.approx(0.5)

    ground = p3d.Body(p3d.Box(10, 1), Vec2(0, 10))
    ball = p3d.Body(p3d.Circle(1), Vec2(0, 8.5))
    contact = p3d.collide(ground, ball)
    assert contact is not None
    assert contact.normal.y == pytest.approx(-1.0)


def test_gravity_and_resting_contact():
    world, _ = world_with_ground()
    ball = world.add(p3d.Body(p3d.Circle(1), Vec2(0, 0), restitution=0.0))
    for _ in range(300):
        world.step()
    assert 7.9 < ball.position.y < 8.2
    assert abs(ball.velocity.y) < 0.5


def test_bounce_loses_height_and_stops():
    world, _ = world_with_ground()
    ball = world.add(p3d.Body(p3d.Circle(1), Vec2(0, 8), restitution=0.6))
    ball.velocity = Vec2(0, 120)
    heights = []
    for _ in range(200):
        world.step()
        heights.append(ball.position.y)
    assert 8 - min(heights) > 1.5
    assert abs(ball.velocity.y) < 1.0


def test_fast_body_does_not_tunnel_through_a_thin_platform():
    world = p3d.PhysicsWorld(gravity=(0, 900))
    world.add(p3d.Body(p3d.Box(50, 0.2), Vec2(0, 10), static=True))
    ball = world.add(p3d.Body(p3d.Circle(0.4), Vec2(0, 0)))
    ball.velocity = Vec2(0, 4000)
    for _ in range(120):
        world.step()
    assert ball.position.y < 12, ball.position.y


def test_raycast_hits_nearest_body_and_misses_cleanly():
    world = p3d.PhysicsWorld(gravity=(0, 0))
    near = world.add(p3d.Body(p3d.Circle(1), Vec2(5, 0), static=True, name="near"))
    far = world.add(p3d.Body(p3d.Box(2, 2), Vec2(20, 0), static=True, name="far"))
    hit = world.raycast(Vec2(0, 0), Vec2(1, 0))
    assert hit is not None and hit.body is near
    assert hit.distance == pytest.approx(4.0)

    box_hit = world.raycast(Vec2(0, 0), Vec2(1, 0.0001), max_distance=1000)
    assert box_hit is not None
    assert world.raycast(Vec2(0, 0), Vec2(0, 1), max_distance=5) is None
    with pytest.raises(ValueError):
        world.raycast(Vec2(0, 0), Vec2(0, 0))


def test_layers_filter_contacts():
    world = p3d.PhysicsWorld(gravity=(0, 0))
    a = world.add(p3d.Body(p3d.Box(2, 2), Vec2(0, 0), layer=1, mask=2, gravity_scale=0.0, static=True))
    b = world.add(p3d.Body(p3d.Box(2, 2), Vec2(1, 0), layer=4, mask=1, gravity_scale=0.0))
    assert world.step() == []
    b.mask = 0xFFFFFFFF
    a.mask = 0xFFFFFFFF
    assert world.step()


def test_triggers_report_without_resolving():
    world = p3d.PhysicsWorld(gravity=(0, 0))
    door = world.add(p3d.Body(p3d.Box(1, 1), Vec2(0, 0), is_trigger=True, static=True))
    player = world.add(p3d.Body(p3d.Box(1, 1), Vec2(0, 0)))
    contacts = world.step()
    assert len(contacts) == 1 and contacts[0].is_trigger
    assert player.position == Vec2(0, 0)


def test_overlap_query_and_removal():
    world = p3d.PhysicsWorld(gravity=(0, 0))
    body = world.add(p3d.Body(p3d.Circle(2), Vec2(3, 3)))
    assert body in world.overlap(Vec2(3, 4))
    assert world.overlap(Vec2(30, 30)) == []
    assert world.remove(body) is True
    assert world.remove(body) is False


def test_simulation_is_deterministic():
    def run():
        world = p3d.PhysicsWorld(gravity=(0, 900))
        world.add(p3d.Body(p3d.Box(50, 1), Vec2(0, 20), static=True))
        ball = world.add(p3d.Body(p3d.Circle(1), Vec2(0, 0), restitution=0.4))
        for _ in range(120):
            world.step()
        return ball.position.x, ball.position.y

    assert run() == run()
