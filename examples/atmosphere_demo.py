"""Dusk, fog, a lightning storm and a reflecting river - all simulated."""

from __future__ import annotations

import py3dgame as p3d


def main() -> None:
    game = p3d.Game(title="py3dgame - atmosphere", width=96, height=64, fps=60)
    canvas = game.canvas

    clock = p3d.DayNightCycle(start_hour=17.5, day_length_hours=2.0)
    fog = p3d.Fog(p3d.FogSettings(density=0.45, horizon=0.62))
    storm = p3d.Lightning(seed=5)
    water = p3d.WaterSurface(axis_y=44, opacity=0.5, ripple=1.6)
    sky = p3d.Sky()

    strikes = 0

    @game.on_update
    def update(dt: float) -> None:
        nonlocal strikes
        clock.advance(dt)
        storm.update(dt)
        water.update(dt)
        strikes += 1
        if strikes % 55 == 0:
            storm.trigger(intensity=0.85, duration=0.25)

    @game.on_draw
    def draw(draw_canvas: p3d.Canvas) -> None:
        state = clock.state()
        sky.draw(draw_canvas, state)
        # village silhouette + river bank
        draw_canvas.fill_rect(0, 40, 96, 24, (18, 20, 26, 255))
        draw_canvas.fill_rect(10, 30, 10, 10, (26, 28, 34, 255))
        draw_canvas.fill_rect(70, 26, 12, 14, (26, 28, 34, 255))
        draw_canvas.fill_rect(40, 34, 6, 6, (40, 34, 30, 255))

        water.apply(draw_canvas)
        fog.apply(draw_canvas)
        storm.draw(draw_canvas)

        lights = [p3d.Light2D((15, 33), 16, (255, 170, 90), 0.9), p3d.Light2D((74, 30), 18, (255, 150, 80), 0.8)]
        lightmap = p3d.build_lightmap(
            draw_canvas.width,
            draw_canvas.height,
            lights,
            p3d.AmbientLight(state.ambient_colour, max(0.12, state.ambient_intensity)),
        )
        lightmap.apply(draw_canvas)

        p3d.ShaderStack(p3d.vignette(0.45)).apply(draw_canvas)

    limit = 240 if isinstance(game.window, p3d.HeadlessWindow) else None
    game.run(max_frames=limit)
    print(
        f"{type(game.window).__name__}: {game.frame_count} frames, hour {clock.hour:.1f}, "
        f"sun {clock.state().sun_intensity:.2f}, strikes {storm.strikes}, "
        f"flash now {storm.level():.2f}"
    )


if __name__ == "__main__":
    main()
