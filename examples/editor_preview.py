"""Save a scene document, render it, optionally serve a live preview.

    python examples/editor_preview.py
    python examples/editor_preview.py --serve --port 8080

The preview server renders on demand from the in-memory document, so editing the
JSON and reloading the page shows the change without restarting anything.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import py3dgame as p3d


def build_scene() -> p3d.SceneDocument:
    scene = p3d.SceneDocument("Editor preview")
    scene.add_node(p3d.NodeDocument("ground", mesh="plane", position=(0, -0.05, 0),
                                    material={"base_colour": (72, 80, 96), "shading": "lambert"}))
    scene.add_node(p3d.NodeDocument("crate", mesh="cube", position=(-1.4, 0.8, 0),
                                    rotation=(0, 18, 0),
                                    material={"base_colour": (226, 132, 74), "shading": "blinn", "roughness": 0.3}))
    scene.add_node(p3d.NodeDocument("marker", mesh="cube", position=(1.5, 0.8, 0.2),
                                    rotation=(0, -22, 0), scale=(0.8, 1.4, 0.8),
                                    material={"base_colour": (110, 190, 214), "shading": "toon"}))
    scene.add_light({"type": "directional", "direction": [0.4, -1.0, -0.3], "intensity": 1.0})
    scene.add_light({"type": "point", "position": [-2.5, 2.2, 2.0], "colour": [120, 170, 255],
                     "intensity": 8.0, "reach": 9.0})
    return scene


def main() -> None:
    parser = argparse.ArgumentParser(description="py3dgame scene preview")
    parser.add_argument("--out", default="out/scene.json")
    parser.add_argument("--png", default="out/scene_preview.png")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    scene = build_scene()
    scene_path = scene.save(args.out)
    image = p3d.render_document(scene, 640, 360)
    image.save(args.png)
    print(f"scene  {scene_path}")
    print(f"render {args.png}  ({image.width}x{image.height})")

    if args.serve:
        server = p3d.PreviewServer(scene, port=args.port)
        print(f"preview {server.url}  (Ctrl+C to stop)")
        server.serve_forever()


if __name__ == "__main__":
    main()
