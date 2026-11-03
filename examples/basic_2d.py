"""A bouncing square: fixed timestep, action bindings, held-key input.

    pip install "py3dgame[window]"
    python examples/basic_2d.py

Arrow keys steer, Escape quits. Headless runs a fixed number of frames so the
example is runnable (and testable) on a server.
"""

from __future__ import annotations

import py3dgame as p3d

WIDTH, HEIGHT = 640, 360
SIZE = 48


def main() -> None:
    game = p3d.Game(title="Bouncing Square", width=WIDTH, height=HEIGHT, fps=60)
    scene = p3d.Scene("Playground")
    scene.background = (10, 12, 20, 255)
    game.load_scene(scene)
    game.input.bind_action("quit", "escape")
    game.input.bind_action("left", "left", "a")
    game.input.bind_action("right", "right", "d")

    player = scene.add(p3d.Node("player"))
    velocity = p3d.Vec2(170.0, 120.0)
    position = p3d.Vec2(WIDTH / 2 - SIZE / 2, HEIGHT / 2 - SIZE / 2)

    @game.on_update
    def move(dt: float) -> None:
        nonlocal position
        if game.input.action_down("left"):
            velocity.x -= 320.0 * dt
        if game.input.action_down("right"):
            velocity.x += 320.0 * dt
        velocity.y += 60.0 * dt  # gentle drift so the square keeps moving
        position = p3d.Vec2(position.x + velocity.x * dt, position.y + velocity.y * dt)
        if position.x <= 0 or position.x + SIZE >= WIDTH:
            velocity.x = -velocity.x
            position.x = max(0.0, min(position.x, WIDTH - SIZE))
        if position.y <= 0 or position.y + SIZE >= HEIGHT:
            velocity.y = -velocity.y
            position.y = max(0.0, min(position.y, HEIGHT - SIZE))
        player.transform.position = p3d.Vec3(position.x, position.y, 0.0)
        if game.input.action_pressed("quit"):
            game.stop()

    @game.on_draw
    def draw(canvas: p3d.Canvas) -> None:
        canvas.fill_rect(int(position.x), int(position.y), SIZE, SIZE, (90, 200, 250))
        canvas.draw_rect(int(position.x), int(position.y), SIZE, SIZE, (255, 255, 255))

    headless = isinstance(game.window, p3d.HeadlessWindow)
    game.run(max_frames=240 if headless else None)
    print(f"{type(game.window).__name__}: {game.frame_count} frames, "
          f"square at ({position.x:.1f}, {position.y:.1f})")


if __name__ == "__main__":
    main()
