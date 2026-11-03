# Roadmap and status

Last updated with release **0.4.0**.

## Implemented

| Area | Status | Where |
| --- | --- | --- |
| Window, game loop, input, scene graph | implemented | `core/`, `platform/`, `input/` |
| 2D canvas, sprites, animation | implemented | `renderer2d/` |
| PNG decode/encode, images | implemented | `renderer2d/image.py` |
| 2D additive lighting | implemented | `renderer2d/lighting2d.py` |
| Atmosphere: sky, fog, lightning, reflection, shaders | implemented | `renderer2d/` |
| Day/night clock, fire grid, destruction | implemented | `world/` |
| 2D rigid bodies, CCD, raycasts | implemented | `physics/` |
| 3D maths: Vec4, Mat3, Quaternion, Transform3D, Frustum | implemented | `math3d.py` |
| Cameras (perspective, orthographic) | implemented | `graphics/camera.py` |
| Indexed meshes, materials, 3D lights | implemented | `graphics/`, `lighting/` |
| Software rasteriser: clipping, culling, depth, PC interpolation | implemented | `graphics/rasterizer.py` |
| Six shading models incl. simplified PBR | implemented | `lighting/shading.py` |

## Next (in spec order)

| Release | Scope | Notes |
| --- | --- | --- |
| 0.5.0 | Materials 2.0, textures in the 3D path, shadow maps, tone mapping | needs depth-only pass |
| 0.6.0 | Terrain: heightmap, chunks, LOD, normals | deterministic seeds |
| 0.7.0 | Vegetation instancing, water 3D, weather | batched, no per-plant objects |
| 0.8.0 | ECS, animation, particles, audio | components over the existing scene graph |
| 0.9.0 | World streaming, spatial index, profiler overlay | chunk load/unload |
| 1.0.0 | Integration, benchmarks, docs freeze | only after the above are real |

## Explicitly not done

GPU backends (OpenGL/Vulkan), shadow maps, GI, skeletal animation, audio,
terrain, particles, ECS, world streaming, editor. None of these are exported
from the package, so importing them fails loudly instead of silently doing
nothing.
