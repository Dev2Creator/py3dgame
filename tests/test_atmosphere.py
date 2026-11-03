"""Sky, fog, lightning, reflections and post-processing shaders."""

from __future__ import annotations

import math

import pytest

import py3dgame as p3d


def _noon_state():
    clock = p3d.DayNightCycle()
    clock.set_hour(12.0)
    return clock.state()


def _midnight_state():
    clock = p3d.DayNightCycle()
    clock.set_hour(1.0)
    return clock.state()


def test_sky_draws_a_gradient_and_a_sun_disc():
    canvas = p3d.Canvas(40, 30)
    p3d.Sky().draw(canvas, _noon_state())

    assert canvas.get_pixel(0, 0)[:3] != canvas.get_pixel(0, 29)[:3]
    bright = sum(
        1
        for y in range(30)
        for x in range(12, 28)
        if sum(canvas.get_pixel(x, y)[:3]) > 600
    )
    assert bright > 5, "the sun disc should be visible near the centre"


def test_sky_shows_stars_at_night():
    canvas = p3d.Canvas(40, 30)
    p3d.Sky().draw(canvas, _midnight_state())

    assert sum(canvas.get_pixel(0, 0)[:3]) < 120
    stars = sum(
        1 for y in range(18) for x in range(40) if sum(canvas.get_pixel(x, y)[:3]) > 200
    )
    assert stars > 0


def test_sky_settings_are_validated():
    with pytest.raises(ValueError):
        p3d.SkySettings(haze_height=1.5)
    with pytest.raises(ValueError):
        p3d.SkySettings(sun_radius=0)


def test_fog_density_zero_leaves_the_frame_alone():
    canvas = p3d.Canvas(8, 8)
    canvas.clear((10, 20, 30, 255))
    p3d.Fog(p3d.FogSettings(density=0.0)).apply(canvas)
    assert canvas.get_pixel(0, 7)[:3] == (10, 20, 30)


def test_fog_thickens_towards_the_horizon():
    canvas = p3d.Canvas(8, 10)
    canvas.clear((0, 0, 0, 255))
    fog = p3d.Fog()
    fog.apply(canvas)

    assert canvas.get_pixel(0, 0)[:3] == (0, 0, 0)
    assert sum(canvas.get_pixel(0, 9)[:3]) > 0
    assert fog.blend(0.9) > fog.blend(0.2)


def test_fog_rejects_impossible_density():
    with pytest.raises(ValueError):
        p3d.FogSettings(density=2.0)


def test_lightning_flash_decays_and_expires():
    lightning = p3d.Lightning()
    lightning.trigger(0.9)

    assert lightning.level() > 0.5
    assert lightning.strikes == 1
    lightning.update(1.0)
    assert lightning.level() == 0.0


def test_lightning_stacks_but_stays_bounded():
    lightning = p3d.Lightning()
    lightning.trigger(0.8)
    lightning.trigger(0.9)
    assert 0.0 < lightning.level() <= 1.0


def test_lightning_validation():
    lightning = p3d.Lightning()
    with pytest.raises(ValueError):
        lightning.trigger(0.0)
    with pytest.raises(ValueError):
        lightning.update(-0.5)


def test_lightning_glow_and_bolt_touch_pixels():
    canvas = p3d.Canvas(24, 24)
    canvas.clear((0, 0, 0, 255))
    lightning = p3d.Lightning()
    lightning.trigger(1.0)
    lightning.draw(canvas)
    lightning.draw_bolt(canvas, 12)

    lit = sum(1 for y in range(24) for x in range(24) if sum(canvas.get_pixel(x, y)[:3]) > 0)
    assert lit > 20


def test_water_mirrors_above_the_axis():
    canvas = p3d.Canvas(16, 16)
    canvas.fill_rect(0, 0, 16, 6, (200, 40, 40))
    p3d.WaterSurface(axis_y=8, opacity=0.8).apply(canvas)

    assert canvas.get_pixel(0, 15)[:3] == (160, 32, 32)
    assert canvas.get_pixel(0, 10)[:3] == (160, 32, 32)
    assert canvas.get_pixel(0, 9)[:3] == (0, 0, 0)


def test_water_opacity_zero_is_a_noop():
    canvas = p3d.Canvas(8, 8)
    canvas.fill_rect(0, 0, 8, 2, (255, 255, 255))
    p3d.WaterSurface(axis_y=4, opacity=0.0).apply(canvas)
    assert canvas.get_pixel(0, 7)[:3] == (0, 0, 0)


def test_water_ripple_animates_the_mirror():
    def render(phase_steps: int):
        canvas = p3d.Canvas(24, 16)
        canvas.fill_rect(4, 0, 3, 6, (255, 255, 255))
        surface = p3d.WaterSurface(axis_y=8, opacity=1.0, ripple=3.0)
        surface.update(phase_steps * 0.5)
        surface.apply(canvas)
        return [canvas.get_pixel(x, 12)[:3] for x in range(24)]

    assert render(0) != render(3)


def test_water_validation():
    with pytest.raises(ValueError):
        p3d.WaterSurface(axis_y=0)
    with pytest.raises(ValueError):
        p3d.WaterSurface(axis_y=4, opacity=1.5)


def test_grayscale_shader_equalises_channels():
    canvas = p3d.Canvas(4, 4)
    canvas.clear((10, 120, 220, 255))
    p3d.grayscale().apply(canvas)

    r, g, b, _ = canvas.get_pixel(0, 0)
    assert abs(r - g) <= 1 and abs(g - b) <= 1


def test_tint_shader_pushes_towards_the_colour():
    canvas = p3d.Canvas(4, 4)
    canvas.clear((100, 100, 100, 255))
    p3d.tint((255, 0, 0)).apply(canvas)

    r, g, _, _ = canvas.get_pixel(0, 0)
    assert r > 100 and g < 100


def test_vignette_darkens_corners_more_than_the_centre():
    canvas = p3d.Canvas(21, 21)
    canvas.clear((200, 200, 200, 255))
    p3d.vignette(0.8).apply(canvas)

    corner = sum(canvas.get_pixel(0, 0)[:3])
    centre = sum(canvas.get_pixel(10, 10)[:3])
    assert corner < centre


def test_scanlines_darken_alternating_rows():
    canvas = p3d.Canvas(4, 6)
    canvas.clear((200, 200, 200, 255))
    p3d.scanlines(spacing=2, strength=0.5).apply(canvas)

    assert sum(canvas.get_pixel(0, 0)[:3]) < sum(canvas.get_pixel(0, 1)[:3])


def test_posterize_limits_the_number_of_levels():
    canvas = p3d.Canvas(16, 1)
    for x in range(16):
        canvas.set_pixel(x, 0, (x * 16, x * 16, x * 16, 255))
    p3d.posterize(levels=3).apply(canvas)

    distinct = {canvas.get_pixel(x, 0)[0] for x in range(16)}
    assert len(distinct) <= 3


def test_shader_stack_composes_in_order():
    canvas = p3d.Canvas(4, 4)
    canvas.clear((10, 120, 220, 255))
    stack = p3d.ShaderStack(p3d.grayscale()).add(p3d.tint((255, 0, 0), strength=1.0))
    stack.apply(canvas)

    r, g, _, _ = canvas.get_pixel(0, 0)
    assert r > g, "tint should run after grayscale"


def test_custom_shader_receives_coordinates():
    seen = []
    canvas = p3d.Canvas(3, 2)

    def fn(x, y, pixel):
        seen.append((x, y))
        return pixel

    p3d.Shader(fn).apply(canvas)
    assert len(seen) == 6 and (2, 1) in seen
