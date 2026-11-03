"""Dunia-inspired systems: day/night clock, fire spread, destruction."""

from __future__ import annotations

import math

import pytest

import py3dgame as p3d
from py3dgame.math3d import Vec2


def test_noon_is_bright_and_midnight_is_dark():
    cycle = p3d.DayNightCycle(latitude=22.5)
    cycle.set_hour(12.0)
    noon = cycle.state()
    assert noon.elevation > 70
    assert noon.sun_intensity == pytest.approx(1.0, abs=0.05)

    cycle.set_hour(0.0)
    midnight = cycle.state()
    assert midnight.elevation < 0
    assert midnight.sun_intensity == 0.0
    assert midnight.ambient_intensity < noon.ambient_intensity


def test_dawn_is_warmer_than_noon():
    cycle = p3d.DayNightCycle()
    cycle.set_hour(6.5)
    dawn = cycle.state().sun_colour
    cycle.set_hour(12.0)
    noon = cycle.state().sun_colour
    assert dawn[0] > dawn[2]
    assert dawn[0] - dawn[2] > noon[0] - noon[2]


def test_clock_advances_wraps_and_rejects_negative_time():
    cycle = p3d.DayNightCycle(start_hour=23.0)
    assert cycle.advance(3600) == pytest.approx(0.0)
    assert cycle.day == 1
    assert cycle.set_hour(25.0) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        cycle.advance(-1)
    with pytest.raises(ValueError):
        p3d.DayNightCycle(start_hour=24.0)


def test_sun_direction_is_unit_length():
    cycle = p3d.DayNightCycle()
    cycle.set_hour(9.0)
    assert cycle.sun_direction().length() == pytest.approx(1.0)


def test_fire_ignites_validates_and_spreads():
    grid = p3d.FireGrid(15, 15, moisture=0.05)
    assert grid.ignite(7, 7) is True
    assert grid.ignite(7, 7) is False
    with pytest.raises(IndexError):
        grid.ignite(99, 0)

    for _ in range(25):
        stats = grid.step(0.2)
    assert stats.burning + stats.burnt >= 4
    assert stats.spread_events >= 3


def test_fire_burns_out_and_is_deterministic():
    def run():
        grid = p3d.FireGrid(12, 12, seed=99)
        grid.ignite(6, 6)
        for _ in range(220):
            grid.step(0.2)
        return grid.stats()

    first, second = run(), run()
    assert first == second
    assert first.burning == 0
    assert first.burnt > 0


def test_wind_pushes_fire_downwind():
    def centroid(direction):
        grid = p3d.FireGrid(21, 21, moisture=0.02, wind=direction, spread_rate=2.0, seed=5)
        grid.ignite(10, 10)
        for _ in range(20):
            grid.step(0.1)
        cells = [
            (index % grid.width)
            for index, state in enumerate(grid.state)
            if state in (p3d.BURNING, p3d.BURNT)
        ]
        return sum(cells) / len(cells)

    assert centroid((1.0, 0.0)) > centroid((-1.0, 0.0))


def test_destruction_states_and_debris():
    crate = p3d.Destructible("crate", health=100)
    assert crate.state == "intact" and crate.debris == 0
    assert crate.damage(40) == "damaged"
    assert crate.damage(30) == "critical"
    assert crate.debris > 0
    assert crate.damage(100) == "destroyed"
    assert crate.ratio == 0.0

    crate.repair(50)
    assert crate.state == "damaged"
    crate.repair(1000)
    assert crate.health == crate.max_health
    with pytest.raises(ValueError):
        crate.damage(-1)


def test_radial_damage_falls_off_and_respects_radius():
    system = p3d.DestructionSystem()
    near = system.register(p3d.Destructible("near", position=Vec2(0, 0)))
    far = system.register(p3d.Destructible("far", position=Vec2(8, 0)))
    outside = system.register(p3d.Destructible("outside", position=Vec2(50, 0)))

    results = dict(system.damage_at(Vec2(0, 0), radius=10, amount=100))
    assert results["near"] == "destroyed"
    assert near.health < far.health
    assert "outside" not in results, "items beyond the radius must not be touched"
    assert outside.health == 100
    assert [item.name for item in system.destroyed] == ["near"]

    with pytest.raises(ValueError):
        system.damage_at(Vec2(0, 0), radius=0, amount=10)


def test_destruction_reset_restores_everything():
    system = p3d.DestructionSystem()
    crate = system.register(p3d.Destructible("crate", health=50))
    system.damage_at(Vec2(0, 0), radius=5, amount=500)
    assert crate.state == "destroyed"
    system.reset()
    assert crate.state == "intact" and crate.health == 50
    assert math.isclose(crate.ratio, 1.0)
