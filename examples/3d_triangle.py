"""Render a single 3D triangle to a PNG.

    python examples/3d_triangle.py

No window is opened: the software renderer writes a framebuffer, which is exactly
what the tests do.
"""

from __future__ import annotations

from pathlib import Path

import py3dgame as p3d


def main() -> None:
    renderer = p3d.SoftwareRenderer(
        width=320,
        height=200,
        camera=p3d.PerspectiveCamera(60, 1.6, 0.5, 50, position=(0, 0.4, 3.2)).look_at(p3d.Vec3(0, 0, 0)),
    )
    renderer.background = (14, 16, 22, 255)
    renderer.lights = [p3d.DirectionalLight(direction=p3d.Vec3(0.2, -0.6, -1.0), intensity=1.0)]
    renderer.clear()
    renderer.draw(
        p3d.Mesh.triangle(1.8),
        p3d.Transform3D(),
        p3d.Material(base_colour=(232, 148, 86), shading="lambert"),
    )
    path = Path("out/3d_triangle.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    renderer.save_png(path)
    stats = renderer.stats
    print(f"{path}  triangles={stats.triangles_drawn}/{stats.triangles_submitted} fragments={stats.fragments}")


if __name__ == "__main__":
    main()
