"""A Dunia-flavoured demo: night falling, a fire front, physics and lighting.

Everything here is a real simulation - no recorded animation. Run it headless:

    python examples/dunia_demo.py

With a display and pygame installed it opens a window; otherwise it renders a
fixed number of frames and reports what happened.
"""

from __future__ import annotations

import py3dgame as p3d


def main() -> None:
    width, height = 96, 64
    game = p3d.Game(title="py3dgame - Dunia demo", width=width, height=height, fps=60)
    scene = p3d.Scene("Dunia demo")
    game.load_scene(scene)

    world = p3d.PhysicsWorld(gravity=(0.0, 700.0))
    world.add(p3d.Body(p3d.Box(width / 2, 4.0), p3d.Vec2(width / 2, height - 4.0), static=True))
    crate_body = world.add(p3d.Body(p3d.Box(5.0, 5.0), p3d.Vec2(width / 2, 8.0), restitution=0.25))

    fire = p3d.FireGrid(24, 16, moisture=0.1, wind=(0.8, -0.1), seed=21)
    fire.ignite(4, 12)
    clock = p3d.DayNightCycle(start_hour=18.0, day_length_hours=1.0)

    props = p3d.DestructionSystem()
    props.register(p3d.Destructible("hut", health=60.0, position=p3d.Vec2(30.0, height - 20.0)))
    props.register(p3d.Destructible("cart", health=40.0, position=p3d.Vec2(58.0, height - 18.0)))

    @game.on_update
    def simulate(dt: float) -> None:
        clock.advance(dt)
        world.step(dt)
        fire.step(dt * 0.6)
        for x, y in fire.burning_cells()[::6]:
            props.damage_at(p3d.Vec2(x * 4.0, y * 4.0), radius=14.0, amount=30.0 * dt)

    @game.on_draw
    def render(canvas: p3d.Canvas) -> None:
        state = clock.state()
        canvas.clear((state.sky_colour[0] // 3, state.sky_colour[1] // 3, state.sky_colour[2] // 3, 255))

        canvas.fill_rect(0, int(height - 8), width, 8, (36, 28, 24))
        for x, y in fire.burning_cells():
            canvas.fill_rect(x * 4, y * 4, 3, 3, (255, 120, 40))

        crate_x = int(crate_body.position.x - 5)
        crate_y = int(crate_body.position.y - 5)
        canvas.fill_rect(crate_x, crate_y, 10, 10, (150, 110, 70))

        lights = [
            p3d.Light2D((x * 4.0 + 1.5, y * 4.0 + 1.5), 24.0, (255, 150, 60), 0.9)
            for x, y in fire.burning_cells()[::3]
        ]
        lightmap = p3d.build_lightmap(
            canvas.width,
            canvas.height,
            lights,
            p3d.AmbientLight(state.ambient_colour, state.ambient_intensity),
        )
        lightmap.apply(canvas)

    frames = 240 if isinstance(game.window, p3d.HeadlessWindow) else None
    game.run(max_frames=frames)
    stats = fire.stats()
    state = clock.state()
    print(
        f"{type(game.window).__name__}: {game.frame_count} frames, "
        f"hour {state.hour:04.1f}, sun {state.sun_intensity:.2f}, "
        f"fire burning {stats.burning} burnt {stats.burnt}, "
        f"destroyed {len(props.destroyed)}"
    )


if __name__ == "__main__":
    main()
