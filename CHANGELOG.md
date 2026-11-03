# Changelog

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
