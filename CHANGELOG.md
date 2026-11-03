# Changelog

## 0.4.0 - 3D pipeline

* `math3d`: `Vec4`, `Mat3`, `Quaternion`, `Transform3D`, `Plane3`, `Frustum`,
  `transform_vec4`, `transform_direction` (2D API untouched)
* `graphics`: `ColorBuffer` with depth, `PerspectiveCamera`, `OrthographicCamera`,
  `Mesh` (triangle/plane/cube), `Vertex`, `Material`, `Rasterizer`, `SoftwareRenderer`
* `lighting`: `DirectionalLight`, `PointLight`, `SpotLight` and six shading models
  (unlit, lambert, phong, blinn, toon, simplified PBR)
* Rasteriser: near-plane clipping, backface culling, depth test,
  perspective-correct UV/normal/world interpolation, per-mesh frustum culling
* `core.scene.Transform` gained `matrix()`/`normal_matrix()` so scene nodes can be
  drawn directly; both transform types are accepted by the renderer
* Examples: `3d_triangle.py`, `rotating_cube.py`; docs: `RENDERING.md`,
  `MATH3D.md`, `ROADMAP.md`
* Tests: 130 passing (25 new)

## 0.3.0 - atmosphere layer

- `Sky` draws a day/night gradient, horizon haze, sun disc and stars from the
  same `SunState` that lights the world.
- `Fog` blends toward a colour with a density and falloff curve, so the same
  parameters can drive a future 3D pipeline.
- `Lightning` provides a flash envelope, screen glow and a jagged bolt.
- `WaterSurface` mirrors the frame across an axis with opacity and animated ripple.
- `Shader` / `ShaderStack` add CPU post-processing: grayscale, tint, vignette,
  scanlines, posterize, plus custom pixel callables.
- 105 tests.


## 0.2.0 - 2026-11-03

Added a real 2D toolchain and Dunia-inspired world simulation.

* PNG decoding and encoding with `zlib` only (8-bit, non-interlaced), image crop
  and flip tests.
* Sprites with scaling, tint, opacity, flipping; sprite sheets and frame
  animation with loop and one-shot modes.
* Additive 2D lighting: per-pixel lightmap, ambient term, apply pass.
* 2D physics: circles and boxes, manifolds, restitution, friction, resting
  stabilisation, continuous collision against thin-platform tunnelling,
  circle/box raycasts, layers/masks, triggers.
* World systems: day/night clock with sun vector and palette; seeded fire grid
  with wind and moisture; destructible props with damage states and debris.
* 84 tests, wheel and sdist rebuilt and installed into a clean venv.
