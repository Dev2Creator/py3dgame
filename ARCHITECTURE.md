# Architecture

## Layering

```
py3dgame/
  platform/      window backends + events        (no engine knowledge)
  input/         device state and action bindings (depends on platform events)
  renderer2d/    software rasteriser into RGBA    (depends on nothing)
  math3d.py      Vec2, Vec3, Mat4                 (depends on nothing)
  core/          scene graph, game loop           (depends on the four above)
  __init__.py    public API surface
```

Dependencies point downward only; `core` never imports a backend directly, it
goes through `platform.window.create_window`. That keeps the editor (future) and
alternative backends replaceable without touching gameplay code.

## Design decisions

**Fixed timestep with an accumulator.** `advance(real_dt)` converts elapsed time
into 0..max_substeps fixed logic steps and exposes `alpha` for interpolation.
Games get deterministic simulation, machines get freedom in frame rate. Backlog
beyond `max_substeps` is dropped (`dropped_steps`) instead of spiralling.

**Headless is a first-class backend, not a mock.** `HeadlessWindow` owns a real
event queue and framebuffer and is what the test-suite drives, so loop and input
behaviour are tested without a display. It is also what servers use.

**A real display is required for "auto".** SDL will happily create an off-screen
surface with no display server; presenting into that would look successful while
showing nothing and receiving no input. `create_window("auto")` therefore checks
for `DISPLAY`/`WAYLAND_DISPLAY`/`SDL_VIDEODRIVER` and falls back to headless.

**Pure-Python maths for now.** Vec3/Mat4 are dependency-free so
`pip install py3dgame` has no native requirements. The 3D renderer will need
bulk transforms; that is the point to add numpy or a native backend behind the
same interface, benchmarked first.

**No speculative public API.** Only implemented systems are exported
(`py3dgame.__all__`). `Mesh`, physics bodies, audio and the editor are absent
rather than stubbed, per the specification's "no dead public APIs" rule.

## Threading and lifecycle

The loop is single-threaded: `pump()` → `advance()` → `draw()` →
`input.end_frame()` → sleep. `run()` always closes the window in a `finally`
block, and `stop()` is safe to call from inside an update hook.

## Testing

50 tests across four files: public API contract, maths identities, scene-graph
semantics, input frame semantics, canvas pixel assertions, window lifecycle,
and loop determinism (`advance`/`drop`/`quit` paths). The pygame backend is
exercised under the SDL `dummy` video driver, so the real backend is covered in
CI without a display.


## 0.2.0 subsystem additions

| Module | Responsibility | Depends on |
| --- | --- | --- |
| `renderer2d/image.py` | PNG encode/decode, RGBA buffers | `zlib`, `struct` |
| `renderer2d/sprite.py` | sprites, sheets, animation | `image`, `canvas` |
| `renderer2d/lighting2d.py` | additive lightmap, ambient | `canvas` |
| `physics/body.py` | shapes, mass, layers, triggers | `math3d` |
| `physics/collision.py` | manifolds for circle/box pairs | `body` |
| `physics/world.py` | integration, contacts, CCD, raycasts | `body`, `collision` |
| `world/daynight.py` | 24h clock, sun vector, palette | `math3d` |
| `world/fire.py` | cellular fire automaton | `math3d`, `random` |
| `world/destruction.py` | health states, radial damage | `math3d` |

Dependency direction stays one-way: `platform` and `renderer2d` never import
`core`; `core` imports both; `physics` and `world` depend only on `math3d` so the
renderer can be replaced without touching simulation code.
