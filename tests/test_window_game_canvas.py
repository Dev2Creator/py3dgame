"""Window backends, the software canvas and the game loop."""

from __future__ import annotations

import pytest

import py3dgame as p3d


# -- canvas ------------------------------------------------------------ #

def test_clear_and_pixel_roundtrip():
    canvas = p3d.Canvas(4, 3)
    canvas.clear((10, 20, 30, 255))
    assert canvas.get_pixel(0, 0) == (10, 20, 30, 255)
    assert canvas.get_pixel(3, 2) == (10, 20, 30, 255)
    canvas.set_pixel(1, 1, (255, 0, 0))
    assert canvas.get_pixel(1, 1) == (255, 0, 0, 255)


def test_pixels_outside_the_canvas_are_clipped():
    canvas = p3d.Canvas(4, 4)
    canvas.set_pixel(-1, 0, (255, 255, 255))
    canvas.set_pixel(99, 99, (255, 255, 255))
    with pytest.raises(IndexError):
        canvas.get_pixel(4, 0)


def test_colour_components_are_validated():
    canvas = p3d.Canvas(2, 2)
    with pytest.raises(ValueError):
        canvas.clear((300, 0, 0))
    with pytest.raises(ValueError):
        canvas.set_pixel(0, 0, (1, 2))
    with pytest.raises(ValueError):
        p3d.Canvas(0, 4)


def test_fill_rect_clips_to_the_frame():
    canvas = p3d.Canvas(10, 10)
    canvas.fill_rect(-2, -2, 4, 4, (255, 0, 0))
    assert canvas.get_pixel(0, 0)[:3] == (255, 0, 0)
    assert canvas.get_pixel(1, 1)[:3] == (255, 0, 0)
    assert canvas.get_pixel(2, 2)[:3] == (0, 0, 0)


def test_draw_rect_draws_only_the_border():
    canvas = p3d.Canvas(10, 10)
    canvas.draw_rect(2, 2, 4, 4, (0, 255, 0))
    assert canvas.get_pixel(2, 2)[:3] == (0, 255, 0)
    assert canvas.get_pixel(5, 2)[:3] == (0, 255, 0)
    assert canvas.get_pixel(3, 3)[:3] == (0, 0, 0)


def test_lines_circles_and_resize():
    canvas = p3d.Canvas(21, 21)
    canvas.draw_line(0, 0, 5, 0, (255, 255, 255))
    assert all(canvas.get_pixel(x, 0)[:3] == (255, 255, 255) for x in range(6))

    canvas.draw_circle(10, 10, 5, (255, 0, 0))
    assert canvas.get_pixel(10, 10)[:3] == (255, 0, 0)
    assert canvas.get_pixel(15, 10)[:3] == (255, 0, 0)
    assert canvas.get_pixel(20, 20)[:3] == (0, 0, 0)

    outline = p3d.Canvas(21, 21)
    outline.draw_circle(10, 10, 5, (0, 0, 255), filled=False)
    assert outline.get_pixel(10, 10)[:3] == (0, 0, 0)
    assert outline.get_pixel(15, 10)[:3] == (0, 0, 255)

    canvas.resize(5, 5)
    assert canvas.size == (5, 5)
    assert canvas.get_pixel(0, 0) == (0, 0, 0, 0)


# -- window ------------------------------------------------------------ #

def test_headless_window_lifecycle():
    window = p3d.HeadlessWindow("Demo", 320, 200)
    assert (window.width, window.height) == (320, 200)
    assert window.title == "Demo"
    assert window.closed is False

    canvas = p3d.Canvas(320, 200)
    window.present(canvas)
    assert window.frame_count == 1
    assert window.last_canvas is canvas

    window.close()
    assert window.closed is True
    with pytest.raises(p3d.BackendError):
        window.present(canvas)


def test_headless_event_queue_and_resize():
    window = p3d.HeadlessWindow("Demo", 100, 100)
    window.post(p3d.Quit())
    events = window.poll_events()
    assert len(events) == 1 and isinstance(events[0], p3d.Quit)
    assert window.poll_events() == []

    window.resize(200, 150)
    resized = window.poll_events()
    assert isinstance(resized[0], p3d.Resize)
    assert (window.width, window.height) == (200, 150)


def test_create_window_selects_headless_explicitly():
    window = p3d.create_window("Demo", 64, 64, backend="headless")
    assert isinstance(window, p3d.HeadlessWindow)
    window.close()


def test_pygame_backend_renders_a_frame(monkeypatch):
    pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    try:
        window = p3d.PygameWindow("Demo", 64, 48)
    except p3d.BackendError as exc:  # pragma: no cover - depends on the host
        pytest.skip(f"no usable SDL video driver: {exc}")
    try:
        canvas = p3d.Canvas(64, 48)
        canvas.clear((0, 128, 255))
        window.present(canvas)
        assert window.frame_count == 1
        assert window.poll_events() == []
    finally:
        window.close()


# -- game loop --------------------------------------------------------- #

def test_step_updates_scene_and_time():
    game = p3d.Game(width=64, height=48, window="headless")
    scene = p3d.Scene("main")
    seen = []
    node = scene.add(p3d.Node("player"))
    node.on_update = lambda dt: seen.append(dt)
    game.load_scene(scene)

    game.step()
    assert seen == [game.fixed_dt]
    assert game.simulated_time == pytest.approx(game.fixed_dt)


def test_advance_accumulates_fixed_steps():
    game = p3d.Game(width=32, height=32, fixed_dt=0.1, window="headless")
    assert game.advance(0.05) == 0
    assert game.alpha == pytest.approx(0.5)
    assert game.advance(0.05) == 1
    assert game.alpha == pytest.approx(0.0)
    assert game.advance(0.35) == 3
    assert game.simulated_time == pytest.approx(0.4)


def test_update_hooks_run_once_per_fixed_step():
    game = p3d.Game(width=32, height=32, fixed_dt=0.1, window="headless")
    seen = []
    game.on_update(lambda dt: seen.append(dt))
    game.advance(0.35)
    assert seen == [pytest.approx(0.1)] * 3


def test_advance_drops_backlog_beyond_max_substeps():
    game = p3d.Game(width=32, height=32, fixed_dt=0.1, max_substeps=2, window="headless")
    steps = game.advance(0.55)
    assert steps == 2
    assert game.dropped_steps == 1
    assert game.alpha == pytest.approx(0.5)


def test_negative_time_is_rejected():
    game = p3d.Game(width=32, height=32, window="headless")
    with pytest.raises(ValueError):
        game.advance(-1)
    with pytest.raises(ValueError):
        game.step(-1)


def test_draw_hooks_and_background():
    game = p3d.Game(width=8, height=8, window="headless")
    scene = p3d.Scene("main")
    scene.background = (1, 2, 3, 255)
    game.load_scene(scene)

    def paint(canvas):
        canvas.fill_rect(0, 0, 2, 2, (255, 255, 0))

    game.on_draw(paint)
    game.draw()
    assert game.frame_count == 1
    assert game.canvas.get_pixel(0, 0)[:3] == (255, 255, 0)
    assert game.canvas.get_pixel(7, 7)[:3] == (1, 2, 3)


def test_run_is_bounded_and_closes_the_window():
    game = p3d.Game(width=32, height=32, fps=1000, window="headless")
    frames = game.run(max_frames=3)
    assert frames == 3
    assert game.window.closed is True


def test_quit_event_stops_the_loop():
    game = p3d.Game(width=32, height=32, fps=1000, window="headless")
    game.window.post(p3d.Quit())
    frames = game.run(max_frames=10)
    assert frames == 1
    assert game.running is False


def test_loading_a_non_scene_is_rejected():
    game = p3d.Game(width=32, height=32, window="headless")
    with pytest.raises(p3d.ConfigurationError):
        game.load_scene("not a scene")
