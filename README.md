# py3dgame

*Create games. Write Python.*

A Python-native game library. This is release **0.1.0**, the runtime foundation:
a real window (or headless surface), a fixed-timestep game loop, input with
action bindings, a scene graph with real transform maths, and a software 2D
rasteriser.

**Status honesty:** 3D rendering, physics, audio, animation, assets, UI and the
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
