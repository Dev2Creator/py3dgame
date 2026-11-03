# Rendering

Status: **implemented, software backend only.**

## Pipeline

```
model matrix -> view -> projection -> clip (near plane)
             -> NDC -> screen -> backface cull -> bounding box
             -> barycentric coverage -> depth test -> perspective-correct
             -> aesthetic shading -> framebuffer
```

Stages live in `graphics/`:

| Stage | Module | Notes |
| --- | --- | --- |
| Pose and projection | `camera.py` | `PerspectiveCamera`, `OrthographicCamera`, `look_at`, frustum |
| Buffers | `framebuffer.py`, `mesh.py` | RGBA colour buffer, float depth buffer, indexed meshes |
| Rasterisation | `rasterizer.py` | near-plane clipping, backface culling, depth test, perspective-correct attributes |
| Shading | `lighting/shading.py` | unlit, lambert, phong, blinn, toon, simplified PBR |
| Orchestration | `renderer.py` | draw calls, frustum culling, statistics, `to_image()`, `save_png()` |

`SoftwareRenderer.capabilities` reports the truth:

```python
{"depth_test": True, "textures": True, "per_pixel_lighting": True,
 "shadow_maps": False, "instancing": False, "msaa": False, "gpu": False}
```

## What is exact, and what is approximate

Exact: projective transform, near-plane clipping, screen-space coverage,
depth ordering, perspective-correct interpolation of world position, normal and
UV, backface winding, mesh indices.

Approximate: PBR is a metallic/roughness approximation with a Fresnel term and
energy conservation, not a reference BRDF. Toon shading is a three-band
quantisation. No shadow maps, no global illumination, no anti-aliasing yet.

## Interpolation detail

Attributes are interpolated as `(attr / w)` and divided by the interpolated
`1 / w`, which is what makes textures and normals correct at oblique angles.
Depth is compared in NDC space, smaller wins.

## Performance honesty

Per-fragment work is Python. Budget roughly 10k-30k fragments per frame for
interactive use on the reference laptop, more for offline stills (the 640x360
hero image above is ~169k fragments and takes a few seconds). Optimisation
targets are recorded in `docs/ROADMAP.md`; the software backend is a
correctness reference, not a promise of 60 FPS on large scenes.

## Adding a backend

Subclass `Renderer`, implement `draw(...)`, publish `capabilities`, and set
`backend_name`. Nothing in `mesh`, `material`, `camera` or the scene layer
depends on the software rasteriser.
