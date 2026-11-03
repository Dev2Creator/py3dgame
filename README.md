# py3dgame

*Create games. Write Python.*

A Python-native game library. This is release **0.3.0**: the runtime foundation, a working 2D toolchain, Dunia-inspired world simulation and an atmosphere layer (sky, fog, lightning, reflections, shaders).
a real window (or headless surface), a fixed-timestep game loop, input with
action bindings, a scene graph with real transform maths, and a software 2D
rasteriser.

**Status honesty:** 3D rendering, 3D physics, audio, skeletal animation, UI and the
editor do **not** exist yet. `AGENTS.md` is the full specification; the roadmap
below lists what is implemented and what is not. No placeholder APIs are exposed
for unimplemented systems.

## Install

```bash
pip install py3dgame                 # runtime, headless-capable, no dependencies
pip install "py3dgame[window]"       # adds pygame for a real OS window
```

## Quickstart

```python
import py3dgame as p3d

game = p3d.Game(title="My Game", width=960, height=540)
scene = p3d.Scene("Main")
player = scene.add(p3d.Node("player", position=p3d.Vec3(0, 0, 0)))
game.load_scene(scene)

@game.on_update
def move(dt):
    player.transform.position.x += 60 * dt

@game.on_draw
def draw(canvas):
    canvas.fill_rect(100, 100, 32, 32, (240, 180, 60))

game.run()
```

## What works today

| Area | State |
| --- | --- |
| Package, wheel, clean-venv install | working |
| Game lifecycle and fixed-timestep loop | working, deterministic tests |
| PNG decode/encode, images, crops | working, no image dependency |
| Sprites, sheets, frame animation | working, pixel-tested |
| 2D lighting lightmap | working, additive with ambient |
| 2D rigid bodies, contacts, raycasts | working, CCD against tunnelling |
| Day/night clock | working, palette + sun vector |
| Fire spread grid | working, wind + moisture, seeded |
| Destructible props | working, damage states + debris |
| Window backends: headless, pygame/SDL2 | working, both tested |
| Input: keys, mouse, wheel, actions, callbacks | working |
| Scene graph: nodes, parenting, transforms, update hooks | working |
| Maths: Vec2, Vec3, Mat4 (translation, rotation, scale, projection) | working |
| 2D rasteriser: clear, rect, line, circle | working |
| 3D renderer, materials, lighting, cartoon shading | not implemented |
| Physics, animation, audio, assets, UI, particles | not implemented |
| Editor | not implemented (deliberately last) |

## Backends

`Game(window=...)` accepts `"auto"`, `"headless"` or `"pygame"`.

* `auto` opens a real window when a display server exists, otherwise headless.
* `headless` never needs SDL, so CI and servers work unmodified.
* Set `PY3DGAME_WINDOW=headless` to force headless.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,window]"
pytest
python examples/hello_world.py
```

From a checkout without installing, run examples with `PYTHONPATH=.`.

## Dunia-inspired systems

`docs/DUNIA.md` maps each Dunia capability to what is implemented here, what is
prototyped, and what is deliberately absent. Short version: the clock, fire and
destruction are real; vegetation, GI, terrain, vehicles and streaming are not.

## Roadmap (spec order)

1. ~~Package foundation~~ (done)
2. ~~Lifecycle, window, input~~ (done)
3. ~~Minimal 2D rasteriser~~ (done, shapes only)
4. 2D sprites, textures, tilemaps
5. 3D renderer, materials, lighting
6. Cartoon/stylised shading
7. Physics backend
8. Animation and skinning
9. Audio
10. UI, particles, editor, packaging extras

## Licence

Proprietary, all rights reserved. See `LICENSE`.

## 3D pipeline

```python
import py3dgame as p3d

renderer = p3d.SoftwareRenderer(
    width=640, height=360,
    camera=p3d.PerspectiveCamera(50, 16 / 9, 0.5, 80, position=(4, 3, 6)).look_at(p3d.Vec3(0, 1, 0)),
)
renderer.lights = [p3d.DirectionalLight(direction=p3d.Vec3(0.4, -1, -0.3), intensity=0.9)]
renderer.draw(p3d.Mesh.cube(1.6), p3d.Transform3D(rotation=p3d.Quaternion.from_euler(0, 30, 0)),
              p3d.Material(base_colour=(228, 132, 74), shading="lambert"))
renderer.save_png("cube.png")
```

Model, view, projection, near-plane clipping, backface culling, depth testing,
perspective-correct interpolation and six shading models. See
[docs/RENDERING.md](docs/RENDERING.md) and [docs/MATH3D.md](docs/MATH3D.md).

## Optional AI runtime

`py3dgame.ai` is provider-neutral and never imported by rendering, physics or
scene code. Chat runs off the game loop: `submit()` returns immediately and
`AIJobSystem.update()` drains finished results inside your fixed step.

```python
runtime = p3d.AIRuntime(p3d.ProviderConfig(provider="ollama", model="llama3"))
jobs = p3d.AIJobSystem(runtime)
jobs.submit([p3d.Message("user", "The ferry is late. React in one line.")])
```

Capabilities are per adapter and honest: the Ollama and OpenAI-compatible
adapters support chat, JSON mode, model listing and usage; streaming, embeddings
and image input are declared unsupported rather than faked. Remote endpoints are
refused unless `allow_remote=True`, keys come from environment variables, and
secrets are redacted from errors.

See `docs/AI_RUNTIME.md` and `docs/ENGINE_STATUS.md`.
