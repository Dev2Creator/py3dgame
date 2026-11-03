# Atmosphere layer

Scope, stated plainly: this is a **screen-space, 2D** atmosphere model. It is
not volumetric fog, not ray-traced reflections, and not a GPU fragment shader
pipeline. The parameters (density, falloff, palette, flash envelope) are shaped
so a future 3D renderer can reuse them instead of inventing a second vocabulary.

## Sky

`Sky(settings).draw(canvas, state, sun_x=0.5)` where `state` is a
`SunState` from `DayNightCycle`.

| Setting | Meaning | Default |
| --- | --- | --- |
| `haze_height` | vertical position of the haze band, 0 (top) to 1 (bottom) | 0.55 |
| `haze_strength` | how strongly the band washes out the gradient | 0.45 |
| `sun_radius` | base disc radius in pixels | 6.0 |
| `star_count` | stars drawn at night | 48 |
| `seed` | deterministic star layout | 7 |

The gradient runs from `sky_colour` at the top to a horizon mix of
`sky_colour` and `sun_colour`. Stars fade in as `sun_intensity` drops below
0.25. The sun disc is skipped when the sun is more than 4 degrees below the
horizon.

## Fog

`Fog(settings).apply(canvas)` and `Fog.blend(depth)` for direct queries.

| Setting | Meaning | Default |
| --- | --- | --- |
| `colour` | fog colour | (198, 206, 214) |
| `density` | maximum blend at full depth, 0..1 | 0.45 |
| `horizon` | frame fraction where fog starts, 0..1 | 0.6 |
| `falloff` | exponent shaping the curve | 2.2 |

## Lightning

`Lightning().trigger(intensity, duration)` then `update(dt)` each frame.
`level()` returns the combined flash brightness (square decay, capped at 1).
`draw(canvas)` adds the glow; `draw_bolt(canvas, x_end)` draws a jagged strike
using a seeded generator, so a replay looks identical.

## Reflections

`WaterSurface(axis_y, opacity, ripple, speed)` mirrors rows above `axis_y`
downwards, blending by `opacity` and shifting by a sine ripple that advances
with `update(dt)`. This is a screen-space trick: it needs something above the
waterline to reflect, which is exactly the case for a 2D scene composed
sky-first.

## Shaders

`Shader(fn)` where `fn(x, y, rgba) -> rgba`, and `ShaderStack` to compose.
Built-ins: `grayscale`, `tint`, `vignette`, `scanlines`, `posterize`.

CPU pixel loops are honest about cost: a 320x180 frame is ~57k Python calls per
pass. Use them for small frames, thumbnails, offline stills and effect
prototyping; the 3D path will move these to a fragment shader.

## Known limitations

- Fog is vertical (depth-cue) rather than per-object distance.
- Reflections are vertical mirrors, not physically based, and do not account
  for surface normals or refraction.
- Lightning does not illuminate the world automatically; feed `level()` into a
  `Light2D` or the ambient intensity if you want it to.
- Shader passes are single-threaded Python.
