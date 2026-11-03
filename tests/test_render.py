"""Images, sprites, animation and 2D lighting."""

from __future__ import annotations

import pytest

import py3dgame as p3d
from py3dgame import renderer2d
from py3dgame.exceptions import AssetNotFoundError, ImageFormatError
from py3dgame.renderer2d.image import Image
from py3dgame.renderer2d.lighting2d import AmbientLight, Light2D, build_lightmap
from py3dgame.renderer2d.sprite import Animation, AnimatedSprite, Sprite, SpriteSheet


def test_png_roundtrip_preserves_pixels(tmp_path):
    image = Image(3, 2)
    image.set_pixel(0, 0, (255, 0, 0, 255))
    image.set_pixel(2, 1, (1, 2, 3, 128))
    restored = Image.from_png(image.to_png())
    assert restored.size() == (3, 2)
    assert restored.get_pixel(0, 0) == (255, 0, 0, 255)
    assert restored.get_pixel(2, 1) == (1, 2, 3, 128)

    saved = image.save(tmp_path / "shot.png")
    assert Image.load(saved).get_pixel(0, 0) == (255, 0, 0, 255)


def test_rejects_bad_images(tmp_path):
    with pytest.raises(ImageFormatError):
        Image.from_png(b"not a png at all")
    with pytest.raises(AssetNotFoundError):
        Image.load(tmp_path / "missing.png")


def test_crop_flip_and_bounds():
    image = Image.solid(4, 2, (10, 20, 30))
    cropped = image.crop(1, 0, 2, 2)
    assert cropped.size() == (2, 2)
    with pytest.raises(ValueError):
        image.crop(3, 1, 5, 5)
    with pytest.raises(IndexError):
        image.get_pixel(9, 0)

    striped = Image(2, 2)
    striped.set_pixel(0, 0, (255, 0, 0, 255))
    flipped = striped.flip_x()
    assert flipped.get_pixel(1, 0) == (255, 0, 0, 255)
    assert flipped.get_pixel(0, 0) == (0, 0, 0, 0)


def test_sprite_draws_scaled_tinted_and_clipped():
    canvas = p3d.Canvas(16, 16)
    sprite = Sprite(Image.solid(2, 2, (200, 100, 50)), position=(4, 4), size=(6, 6))
    sprite.draw(canvas)
    assert canvas.get_pixel(5, 5)[:3] == (200, 100, 50)
    assert canvas.get_pixel(0, 0) == (0, 0, 0, 0)

    tinted = Sprite(Image.solid(2, 2, (200, 100, 50)), position=(0, 0), tint=(255, 0, 0))
    tinted.draw(canvas)
    assert canvas.get_pixel(0, 0)[:3] == (200, 0, 0)

    clear_canvas = p3d.Canvas(16, 16)
    transparent = Sprite(Image.solid(2, 2), position=(8, 8), opacity=0.0)
    transparent.draw(clear_canvas)
    assert clear_canvas.get_pixel(8, 8)[3] == 0


def test_sprite_sheet_and_animation_timing():
    sheet_image = Image(4, 2)
    for x in range(4):
        for y in range(2):
            sheet_image.set_pixel(x, y, (x * 60, y * 120, 0, 255))
    sheet = SpriteSheet(sheet_image, frame_width=2, frame_height=1)
    assert sheet.frame_count == 4
    assert sheet.frame(0).get_pixel(0, 0)[0] == 0
    assert sheet.frame(1).get_pixel(0, 0)[0] == 120
    with pytest.raises(IndexError):
        sheet.frame(99)

    animation = Animation([sheet.frame(0), sheet.frame(1)], durations=0.1, loop=True)
    assert animation.current().get_pixel(0, 0)[0] == 0
    animation.update(0.15)
    assert animation.current().get_pixel(0, 0)[0] == 120
    animation.update(0.2)  # 0.35s total: frame 3 of 2 -> index 1 again
    assert animation.current().get_pixel(0, 0)[0] == 120

    once = Animation([sheet.frame(0), sheet.frame(1)], durations=0.1, loop=False)
    once.update(0.5)
    assert once.finished
    assert once.current().get_pixel(0, 0)[0] == 120

    animated = AnimatedSprite(Animation([sheet.frame(0), sheet.frame(1)], durations=0.1))
    animated.update(0.12)
    assert animated.image.get_pixel(0, 0)[0] == 120


def test_lightmap_falloff_and_ambient():
    lightmap = build_lightmap(32, 32, [Light2D((16, 16), 12)], AmbientLight(intensity=0.2))
    centre = lightmap.get(16, 16)
    edge = lightmap.get(31, 31)
    assert centre[0] == pytest.approx(1.0)
    assert edge[0] == pytest.approx(0.2)
    assert lightmap.get(20, 16)[0] < centre[0]

    with pytest.raises(ValueError):
        build_lightmap(4, 4, [Light2D((0, 0), 0)])


def test_lightmap_multiplies_the_frame():
    canvas = p3d.Canvas(8, 8)
    canvas.clear((200, 100, 50, 255))
    lightmap = build_lightmap(8, 8, [], AmbientLight(intensity=0.5))
    lightmap.apply(canvas)
    assert canvas.get_pixel(0, 0)[:3] == (100, 50, 25)


def test_two_lights_accumulate_but_clamp():
    lights = [Light2D((16, 16), 20), Light2D((16, 16), 20)]
    lightmap = build_lightmap(32, 32, lights, AmbientLight(intensity=0.0))
    assert lightmap.get(16, 16)[0] <= 1.0


def test_public_renderer_surface_is_exported():
    for name in ("Canvas", "Image", "Sprite", "SpriteSheet", "Animation", "AnimatedSprite", "Light2D"):
        assert hasattr(p3d, name), name
    assert renderer2d.Canvas is p3d.Canvas
