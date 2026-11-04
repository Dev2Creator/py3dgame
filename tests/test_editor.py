"""Scene documents, preview rendering and the preview server."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

import py3dgame as p3d
from py3dgame.editor import NodeDocument, PreviewServer, SceneDocument, render_document, render_document_png


def _scene() -> SceneDocument:
    scene = SceneDocument("studio")
    scene.add_node(NodeDocument("crate", material={"base_colour": (200, 120, 60), "shading": "blinn"}))
    scene.add_light({"type": "directional", "direction": [0.4, -1.0, -0.3]})
    return scene


def test_node_roundtrip_preserves_values():
    node = NodeDocument("a", mesh="plane", position=(1, 2, 3), scale=(2, 2, 2), material={"shading": "toon"})
    clone = NodeDocument.from_dict(node.to_dict())
    assert clone.id == "a" and clone.mesh == "plane"
    assert clone.position == (1.0, 2.0, 3.0) and clone.scale == (2.0, 2.0, 2.0)


def test_unknown_mesh_is_rejected():
    with pytest.raises(p3d.DocumentError):
        NodeDocument("x", mesh="dragon")


def test_non_positive_scale_is_rejected():
    with pytest.raises(p3d.DocumentError):
        NodeDocument("x", scale=(1, 0, 1))


def test_material_typos_are_rejected():
    with pytest.raises(p3d.DocumentError):
        NodeDocument("x", material={"base_color": (1, 2, 3)})


def test_duplicate_node_ids_are_rejected():
    scene = _scene()
    with pytest.raises(p3d.DocumentError):
        scene.add_node(NodeDocument("crate"))


def test_scene_saves_and_loads(tmp_path):
    scene = _scene()
    path = scene.save(tmp_path / "world.json")
    assert json.loads(path.read_text())["nodes"][0]["id"] == "crate"
    clone = SceneDocument.load(path)
    assert clone.name == scene.name and len(clone.nodes) == 1
    assert clone.to_dict() == scene.to_dict()


def test_missing_and_malformed_scene_files_raise(tmp_path):
    with pytest.raises(p3d.DocumentError):
        SceneDocument.load(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(p3d.DocumentError):
        SceneDocument.load(bad)


def test_invalid_camera_and_lights_are_rejected():
    with pytest.raises(p3d.DocumentError):
        SceneDocument("x", fov=200)
    with pytest.raises(p3d.DocumentError):
        SceneDocument("x", lights=[{"type": "laser"}])
    with pytest.raises(p3d.DocumentError):
        SceneDocument("x", lights=[{"type": "directional"}])


def test_rgb_background_is_expanded_to_rgba():
    scene = SceneDocument.from_dict({"name": "s", "background": [1, 2, 3]})
    assert scene.background == (1, 2, 3, 255)


def test_render_document_produces_geometry():
    image = render_document(_scene(), 96, 64)
    assert image.size() == (96, 64)
    background = (18, 20, 30)
    painted = sum(1 for y in range(64) for x in range(96) if image.get_pixel(x, y)[:3] != background)
    assert painted > 100, "the crate should cover a visible part of the frame"


def test_render_png_is_a_png():
    assert render_document_png(_scene(), 64, 48)[:8] == b"\x89PNG\r\n\x1a\n"


def test_preview_server_serves_page_frame_and_scene():
    server = PreviewServer(_scene(), port=0, width=80, height=60).start()
    try:
        page = urllib.request.urlopen(server.url, timeout=10).read()
        assert b"py3dgame preview" in page
        frame = urllib.request.urlopen(server.url + "frame.png", timeout=20).read()
        assert frame[:4] == b"\x89PNG"
        payload = json.loads(urllib.request.urlopen(server.url + "api/scene", timeout=10).read())
        assert payload["name"] == "studio"
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(server.url + "secrets", timeout=10)
    finally:
        server.stop()


def test_preview_server_refuses_non_loopback_binding():
    with pytest.raises(ValueError):
        PreviewServer(_scene(), host="0.0.0.0")


def test_public_editor_surface_is_exported():
    for name in ("SceneDocument", "NodeDocument", "PreviewServer", "render_document", "DocumentError"):
        assert hasattr(p3d, name), name
