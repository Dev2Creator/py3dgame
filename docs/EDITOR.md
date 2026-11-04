# Editor foundation

Status: **partial.** A scene document, a renderer for it and a local preview
server exist and are tested. There is no UI for editing nodes yet.

## What exists

`py3dgame.editor` provides three things:

1. `SceneDocument` / `NodeDocument`: plain JSON scene description. Nodes name a
   built-in mesh (`cube`, `plane`, `triangle`), a transform and material
   properties. Lights are described by value. Everything validates on
   construction and on load, so a bad document fails with `DocumentError`
   instead of a render crash.
2. `render_document(document, width, height)`: one headless render to an `Image`.
3. `PreviewServer`: serves the document at `http://127.0.0.1:<port>/`, with
   `/frame.png` re-rendering on each request and `/api/scene` returning the JSON.

## Document schema

```json
{
  "name": "Editor preview",
  "camera": {"position": [4, 2.8, 5.2], "target": [0, 0.5, 0], "fov": 55},
  "background": [18, 20, 30, 255],
  "nodes": [
    {"id": "crate", "mesh": "cube", "position": [0, 0.8, 0],
     "rotation": [0, 18, 0], "scale": [1, 1, 1],
     "material": {"base_colour": [226, 132, 74], "shading": "blinn"}}
  ],
  "lights": [{"type": "directional", "direction": [0.4, -1, -0.3], "intensity": 1.0}]
}
```

Unknown mesh names, duplicate node ids, non-positive scale, misspelled material
keys and malformed lights are all rejected with a message naming the field.

## Security posture

The preview server binds to loopback only (`ValueError` otherwise), serves GET
routes exclusively, exposes no file paths and has no upload endpoint. Scene
documents are data, never code: nothing in a document is evaluated.

## Not implemented

- Editing UI (node list, inspector, gizmos).
- Undo/redo, multi-scene projects, asset browser.
- Saving from the browser: the server is read-only by design for now.
- Textured or skinned meshes, terrain nodes, spawn points, components.

Those need the entity/component and asset systems first, which is why the
document format keeps nodes declarative rather than pointing at Python objects.
