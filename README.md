# py3dgame

A Python-native game engine: window, fixed-timestep loop, scene graph, 2D toolchain, a real 3D pipeline with a software rasteriser, atmosphere systems and an optional provider-neutral AI runtime.

Pure Python, zero required dependencies. Everything runs headless, so tests and CI do not need a display, a GPU or a network.

```
pip install py3dgame            # once published; see Install for the current route
```

**Status:** 0.6.0, pre-1.0 and deliberately staged. This README states what works and what does not, because a game engine that lies about its features wastes your afternoon.

---

## Why this exists

Most Python game libraries either stop at 2D sprites or wrap a native engine so tightly that you are really writing C++ through Python. py3dgame is being built as a small, readable engine that owns its own maths, its own rasteriser and its own scene graph, and can grow a GPU backend later without a rewrite.

Design commitments:

- **The public Python API is the product.** `import py3dgame` and go.
- **Headless first.** Every subsystem is testable without a display.
- **No fake features.** A name is only exported once it genuinely works.
- **Optional stays optional.** `pygame` is a window extra, not a dependency. The AI subsystem never phones home unless you configure it to.
- **CPU correctness reference.** The software renderer is the truth the future GPU backend will be measured against.

---

## Install

Not on PyPI yet: the name `py3dgame` is held by an unrelated 0.0.1 project, so the distribution route is currently the repository.

```bash
git clone https://github.com/Dev2Creator/py3dgame
cd py3dgame
pip install -e .                 # core, no dependencies
pip install -e ".[window]"      # optional: pygame/SDL2 real window
pip install -e ".[dev]"         # optional: pytest + build tooling
```

Requires Python 3.11 or newer. Tested on Linux, CPython 3.11.

---

## Quickstart: a 2D game

```python
import py3dgame as p3d

game = p3d.Game(title="Hello, py3dgame", width=480, height=270)
scene = p3d.Scene("Main")
scene.background = (16, 18, 24, 255)
square = scene.add(p3d.Node("square", position=p3d.Vec3(60, 60, 0)))
game.load_scene(scene)

speed = p3d.Vec2(90.0, 60.0)

@game.on_update
def update(dt):
    pos = square.transform.position
    pos.x += speed.x * dt
    pos.y += speed.y * dt
    if pos.x < 10 or pos.x > 470:
        speed.x = -speed.x
    if pos.y < 10 or pos.y > 260:
        speed.y = -speed.y

@game.on_draw
def draw(canvas):
    pos = square.transform.position
    canvas.fill_rect(int(pos.x) - 10, int(pos.y) - 10, 20, 20, (240, 180, 60))

# Headless runs need a frame budget; a real window runs until you close it.
limit = 180 if isinstance(game.window, p3d.HeadlessWindow) else None
game.run(max_frames=limit)
```

`speed` is a `Vec2`, so it is mutable in place. The loop is fixed-timestep with an accumulator: `update` always receives the same `dt`, and `game.alpha` gives you the interpolation factor for smooth drawing.

---

## Quickstart: 3D geometry

```python
import py3dgame as p3d

camera = p3d.PerspectiveCamera(55, 16 / 9, 0.5, 100, position=(3.0, 2.4, 4.2))
camera.look_at(p3d.Vec3(0, 0.4, 0))

renderer = p3d.SoftwareRenderer(960, 540, camera)
renderer.lights = [p3d.DirectionalLight(direction=p3d.Vec3(0.4, -1.0, -0.3), intensity=1.0)]

renderer.clear()
renderer.draw(
    p3d.Mesh.cube(1.5),
    p3d.Transform3D(rotation=p3d.Quaternion.from_euler(0, 30, 0)),
    p3d.Material(base_colour=(220, 130, 70), shading="blinn", roughness=0.35),
)
renderer.save_png("cube.png")

print(renderer.stats.triangles_drawn, renderer.stats.fragments)
```

That path is a real pipeline: model, view and projection matrices, near-plane clipping, perspective divide, backface culling, depth testing and perspective-correct interpolation of world position, normal and UV. Not shapes drawn by hand.

Shading models available today: `unlit`, `lambert`, `phong`, `blinn`, `toon`, `pbr` (simplified metallic/roughness with Fresnel and energy conservation).

---

## Quickstart: optional AI, without blocking the loop

```python
import py3dgame as p3d

config = p3d.ProviderConfig(provider="mock", model="mock-small")   # offline, deterministic
runtime = p3d.AIRuntime(config, p3d.MockProvider())
ai = p3d.AIJobSystem(runtime)

ai.submit([p3d.Message("user", "Greet the player in one line.")])

@game.on_update
def update(dt):
    for result in ai.update():
        if result.ok:
            print(result.response.text)
        else:
            print("AI unavailable:", result.error.kind)
```

Switch to a local model by changing one line of configuration:

```python
config = p3d.ProviderConfig(provider="ollama", model="llama3.1:8b", endpoint="http://127.0.0.1:11434")
```

Remote endpoints are refused unless you set `allow_remote=True`, and API keys are read from the environment and redacted from errors. Providers declare capabilities they can actually honour, so `capabilities().streaming` is `False` today rather than a promise.

---

## What works today

Legend: **working** means implemented, tested and exercised by an example. **partial** means it works with documented gaps. **planned** means not implemented, not exported.

| Area | Status | Notes |
| --- | --- | --- |
| Window (headless, pygame/SDL2) | working | `auto` needs a display, otherwise headless |
| Fixed-timestep loop | working | accumulator, substep clamp, alpha |
| Input | working | keys, mouse, wheel, named actions, callbacks |
| Scene graph | working | hierarchy, cycle checks, world matrices |
| 2D canvas | working | rects, lines, circles, blitting |
| PNG images | working | decode/encode via `zlib`, 8-bit, non-interlaced |
| Sprites, sheets, animation | working | nearest-neighbour scaling, tint, opacity |
| 2D lighting | working | additive lightmap, ambient, falloff |
| Sky, fog, lightning | working | driven by the same `SunState` clock |
| Water surface | partial | screen-space mirror plus ripple, not true reflections |
| Post-process shaders | working | grayscale, tint, vignette, scanlines, posterize, custom callables |
| 2D physics | working | circles/boxes, restitution, friction, CCD, raycasts, layers, triggers |
| Day/night clock | working | elevation, palettes, sun direction |
| Fire spread | partial | seeded cellular grid with wind and moisture, 2D only |
| Destruction | working | health states, radial damage falloff |
| 3D maths | working | Vec4, Mat3, Mat4, Quaternion, Transform3D, Frustum |
| Cameras | working | perspective, orthographic, `look_at`, frustum culling |
| Meshes | working | indexed triangles, cube/plane/triangle builders |
| 3D rasteriser | working | clipping, culling, depth test, perspective-correct attributes |
| Materials and shading | partial | six models, texture sampling; no normal maps, no mipmaps |
| 3D lights | working | directional, point, spot with attenuation and cone falloff |
| AI runtime | working | providers, retries, cancellation, queue bounds, stats |
| AI streaming, embeddings, tools | planned | adapters report these as unsupported |
| Shadows, terrain, vegetation | planned | not implemented, not exported |
| ECS, animation, particles | planned | scene graph exists, components do not |
| Audio, world streaming, profiler | planned | not implemented |
| Editor | not planned | the library is the product |

---

| Editor foundation | working: scene documents, headless preview, loopback preview server (no UI yet) |

## Architecture

```
platform/      window backends, events          (no engine imports)
renderer2d/    canvas, images, sprites, lights, atmosphere passes
graphics/      cameras, meshes, materials, rasteriser, renderer
lighting/      3D lights and shading models
math3d         vectors, matrices, quaternions, transforms, frustum
core/          Game loop, Scene, Node
physics/       fixed-step rigid bodies, collision, raycasts
world/         day/night clock, fire grid, destruction
ai/            provider-neutral runtime, adapters, game-loop-safe jobs
input/         keyboard, mouse, actions
```

Dependencies point one way: `platform` and `math3d` know nothing about the rest, `renderer2d` and `graphics` sit above them, `core` composes, `ai` is optional and independent of rendering. There are no cycles, and no module imports a window to be able to draw.

The renderer is split behind a backend boundary: `SoftwareRenderer` is the only implementation today, and it exposes `capabilities` so callers can feature-detect rather than assume. A GPU backend is planned, not pretended.

More detail: [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/RENDERING.md](docs/RENDERING.md).

---

## Examples

Run any example from the repository root after `pip install -e .`.

| Example | Shows |
| --- | --- |
| `examples/hello_world.py` | smallest complete game, scene plus draw hook |
| `examples/basic_2d.py` | fixed-timestep motion and input actions |
| `examples/3d_triangle.py` | first 3D render, single triangle |
| `examples/rotating_cube.py` | 8-frame cube turntable with ground plane |
| `examples/atmosphere_demo.py` | sky, fog, lightning, water, post-processing |
| `examples/dunia_demo.py` | fire spread, destruction, day/night, physics |
| `examples/editor_preview.py` | saves a scene document, renders it, optional live preview |
| `examples/ai_dialogue.py` | AI job submitted from the loop, result polled safely |

All examples run headless and write output they can describe, so they are usable in CI.

---

## Tests

```bash
python -m pytest          # 146 tests
```

The suite covers maths, projections, rasteriser coverage and depth ordering, culling, clipping, mesh integrity, shading behaviour, physics resting and CCD, streaming-free AI adapters against a local stub HTTP server, cancellation, retries and packaging metadata. It is not a claim of full coverage: rendering is verified by pixel assertions, not by image diffing.

---

## Performance, honestly

The 3D renderer is a CPU rasteriser written in Python. A 640x360 frame with three lit objects and a ground plane writes around 170,000 fragments and takes a noticeable fraction of a second. It is a correctness reference, not a path to 60 fps on a large scene.

What that means in practice: use it for tooling, tests, offline renders and learning. Do not expect open-world frame rates until a GPU backend exists. The target hardware assumption for that backend is a mid-range laptop GPU; nothing here is tuned to fake a benchmark.

---

## Roadmap

| Release | Focus |
| --- | --- |
| 0.4.0 | 3D maths, cameras, meshes, software rasteriser (done) |
| 0.5.0 | optional AI runtime and provider adapters (done) |
| 0.6.0 | scene documents and the preview server (done) |
| 0.7.0 | shadow maps, texture pipeline, tone mapping |
| 0.8.0 | entity-component scene system, animation, particles |
| 0.9.0 | terrain, vegetation, world streaming, profiler |
| 1.0.0 | stable integrated engine |

Full detail and the reasoning behind the order: [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Known limitations

- No shadows, no terrain, no vegetation, no water reflections from scene geometry.
- No ECS yet: entities are plain `Node` objects with a transform.
- No audio, no skeletal animation, no particle system, no world streaming.
- Single-threaded renderer; the AI runtime is the only threaded subsystem.
- Distances are metres by convention only; there is no unit enforcement.
- Not on PyPI while the name is occupied upstream.

---

## Documentation

- [docs/ENGINE_STATUS.md](docs/ENGINE_STATUS.md): verified assessment of every subsystem
- [docs/RENDERING.md](docs/RENDERING.md): pipeline stages and limits
- [docs/MATH3D.md](docs/MATH3D.md): conventions, handedness, matrices
- [docs/AI_RUNTIME.md](docs/AI_RUNTIME.md): providers, retries, cancellation, security
- [docs/EDITOR.md](docs/EDITOR.md): scene documents and the preview server
- [docs/ATMOSPHERE.md](docs/ATMOSPHERE.md): sky, fog, lightning, reflection, shaders
- [docs/DUNIA.md](docs/DUNIA.md): world simulation systems
- [docs/ROADMAP.md](docs/ROADMAP.md): staged releases
- [CHANGELOG.md](CHANGELOG.md): what changed, release by release
- [AGENTS.md](AGENTS.md): the engineering brief this repository is built against

---

## Licence

Proprietary, all rights reserved. See [LICENSE](LICENSE). Contact the author for licensing terms.

Author: Anika Mukherjee (Dev2Creator), cuteypieanika@gmail.com

