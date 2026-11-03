# Dunia-inspired systems

Dunia (Far Cry 2's engine) is famous for a world that keeps simulating: a sun
that moves, fire that spreads with the wind, vegetation that bends, and props
that break. This page is an honest map of what that inspiration turned into
inside py3dgame.

| Dunia capability | py3dgame status | Where |
| --- | --- | --- |
| Time of day with sun palette | implemented, tested | `world/daynight.py` |
| Sun/moon direction vector | implemented, tested | `DayNightCycle.sun_direction` |
| Wind-driven fire propagation | implemented as a grid automaton | `world/fire.py` |
| Fire consumes fuel and burns out | implemented, seeded/deterministic | `world/fire.py` |
| Destructible props with damage states | implemented | `world/destruction.py` |
| Radial explosion damage with falloff | implemented | `DestructionSystem.damage_at` |
| Vegetation bending in wind | not implemented | planned with the 3D renderer |
| Dynamic global illumination | not implemented; only additive 2D lightmaps | `renderer2d/lighting2d.py` |
| Terrain, roads, streaming worlds | not implemented | out of scope for 2D |
| Vehicles and ragdolls | not implemented | needs 3D physics |
| Volumetric fog and weather | not implemented; sky colour only | - |
| LOD and culling | not implemented | - |

## Design notes

* **Determinism first.** Fire uses a seeded RNG and a fixed traversal order, so
  a test can assert exact counts. Random visuals are useless in a regression
  test.
* **Simulation without a renderer.** `world/` and `physics/` import only
  `math3d`, so they run headless and can be unit tested without a window.
* **No borrowed content.** Nothing here reuses Dunia assets, data or code; the
  inspiration is purely architectural.
* **Claims are bounded.** The lightmap is a 2D screen-space effect. It is not
  global illumination and the README says so.

## Next steps toward the real thing

1. Shadow casting for the lightmap (occluder list, penumbra approximation).
2. Wind field shared by fire, vegetation and particles instead of per-system
   wind vectors.
3. Heat diffusion into a coarse voxel grid when the 3D renderer lands.
4. Destruction that emits physics debris bodies instead of a debris count.
