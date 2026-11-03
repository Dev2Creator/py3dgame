# Engine status — 0.5.0

Verified against the checked-out repository on 2026-11-03 (Asia/Calcutta) by
running the suite, building distributions and installing the wheel in a clean
virtual environment.

## Baseline

| Item | Verified value |
| --- | --- |
| Distribution / import | `py3dgame` |
| Version | 0.5.0 |
| Python | 3.11+ (`requires-python = >=3.11`) |
| Runtime dependencies | none |
| Optional extras | `window` (pygame), `dev` (pytest, build) |
| Test suite | 146 tests, all passing (pytest) |
| Public names in `py3dgame.__all__` | 106 |
| Wheel + sdist | build cleanly; wheel imports and renders from a clean venv |
| Platforms verified | Linux (headless container). Windows/macOS untested. |

## Package layout

```
py3dgame/
  math3d.py          Vec2/3/4, Mat3/4, Quaternion, Transform3D, Plane3, Frustum
  core/              Game loop, scene graph, node transforms
  platform/          Window backends (headless, pygame), events
  input/             Keyboard, mouse, wheel, action bindings
  renderer2d/        Canvas, PNG images, sprites, lighting2d, sky, fog,
                     lightning, reflection, shader
  graphics/          Cameras, meshes, materials, rasteriser, software renderer
  lighting/          Directional/point/spot lights, shading models
  physics/           Bodies, collision, fixed-step world, raycasts
  world/             Day/night clock, fire grid, destructible props
  ai/                Provider-neutral AI runtime and adapters
```

## Implemented

- Fixed-timestep loop, input, action bindings, headless and pygame windows.
- Scene graph with parenting, cycle detection and world transforms.
- 2D toolchain: PNG decode/encode, sprites, sheets, animation, lightmaps.
- Atmosphere: sky, fog, lightning, water reflection, post-processing shaders.
- 3D maths and a working software 3D pipeline: cameras, meshes, materials,
  near-plane clipping, backface culling, depth buffer, perspective-correct
  interpolation, six shading models, frustum culling, render statistics.
- Physics: circles/boxes, restitution, friction, resting contacts, CCD,
  raycasts, layers, triggers.
- Dunia-inspired world systems: day/night, fire spread, destruction.
- AI runtime: provider contracts, Ollama and OpenAI-compatible adapters, mock
  provider, bounded concurrency, retries with backoff, cancellation, opt-in
  caching, redaction, game-loop-safe job facade.

## Partially implemented

- Lighting is per-fragment on the CPU; no shadows yet.
- AI adapters support chat only. Streaming, embeddings and tool calling are
  declared unsupported rather than stubbed.
- Texture mapping exists in the material/rasteriser path but there is no asset
  pipeline, mipmapping or texture cache.

## Not implemented (and not exported)

Shadow mapping, terrain, vegetation, water 3D surface, ECS, animation, particles,
audio, world streaming, progressive/profiler overlays, NPC simulation, quests,
asset downloading, terrain LOD, GPU backends.

## Risks and constraints

1. The software rasteriser is a correctness reference, not a performance path.
2. Memory grows with per-pixel Python loops; large frames are slow by design.
3. No GPU backend exists, so no claim of hardware acceleration is made.
4. NPC simulation depends on an ECS and terrain that do not exist yet.
5. Remote AI providers are refused unless `allow_remote=True`; local-first is
   the default.

## Milestones from the actual code

- 0.6.0: shadow maps (depth pass + PCF), texture sampling in 3D materials.
- 0.7.0: terrain heightfields, chunking, LOD, vegetation batching.
- 0.8.0: ECS + component scene, animation, particles.
- 0.9.0: world streaming, profiler, asset pipeline.
- 1.0.0: NPC simulation tiers on top of ECS, integrated open-world demo.
