"""Render a rotating, lit cube as a PNG sequence.

    python examples/rotating_cube.py

Every frame is a real 3D render: perspective projection, depth buffer, backface
culling and per-pixel Lambert shading.
"""

from __future__ import annotations

from pathlib import Path

import py3dgame as p3d


def main() -> None:
    out = Path("out/rotating_cube")
    out.mkdir(parents=True, exist_ok=True)
    renderer = p3d.SoftwareRenderer(
        width=320,
        height=240,
        camera=p3d.PerspectiveCamera(50, 4 / 3, 0.5, 60, position=(2.4, 2.0, 3.2)).look_at(p3d.Vec3(0, 0, 0)),
    )
    renderer.lights = [p3d.DirectionalLight(direction=p3d.Vec3(0.4, -1.0, -0.35), intensity=0.9)]
    cube = p3d.Mesh.cube(1.4)
    ground = p3d.Mesh.plane(6.0, 1)
    material = p3d.Material(base_colour=(228, 140, 82), shading="lambert")
    floor = p3d.Material(base_colour=(96, 104, 120), shading="lambert")

    for frame in range(8):
        renderer.clear()
        renderer.draw(ground, p3d.Transform3D(position=(0, -1.0, 0)), floor)
        renderer.draw(cube, p3d.Transform3D(rotation=p3d.Quaternion.from_euler(0, frame * 45, 0)), material)
        renderer.save_png(out / f"frame_{frame:02d}.png")

    print(f"wrote 8 frames to {out}")
    print(f"last frame: triangles={renderer.stats.triangles_drawn}/{renderer.stats.triangles_submitted} "
          f"fragments={renderer.stats.fragments}")


if __name__ == "__main__":
    main()
