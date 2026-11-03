"""The smallest complete py3dgame program.

Run it with a real window:

    pip install "py3dgame[window]"
    python examples/hello_world.py

Without a display it falls back to the headless backend and runs 120 frames.
"""

from __future__ import annotations

import py3dgame as p3d


def main() -> None:
    game = p3d.Game(title="Hello, py3dgame", width=480, height=270, fps=60)
    scene = p3d.Scene("Main")
    scene.background = (16, 18, 24, 255)
    marker = scene.add(p3d.Node("marker", position=p3d.Vec3(0, 0, 0)))
    game.load_scene(scene)

    @game.on_update
    def spin(dt: float) -> None:
        marker.transform.rotation.y = (marker.transform.rotation.y + 45.0 * dt) % 360.0

    @game.on_draw
    def draw(canvas: p3d.Canvas) -> None:
        canvas.fill_rect(40, 40, 96, 96, (240, 180, 60))
        canvas.draw_rect(39, 39, 98, 98, (255, 255, 255))

    headless = isinstance(game.window, p3d.HeadlessWindow)
    game.run(max_frames=120 if headless else None)
    print(f"{type(game.window).__name__}: {game.frame_count} frames, "
          f"{game.simulated_time:.2f}s simulated, rotation {marker.transform.rotation.y:.1f}deg")


if __name__ == "__main__":
    main()
