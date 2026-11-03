# math3d

Status: **implemented** (2D types from 0.1-0.3 unchanged, 3D added in 0.4.0).

| Type | Purpose | Key methods |
| --- | --- | --- |
| `Vec2`, `Vec3` | points, directions | `dot`, `cross`, `length`, `normalized` |
| `Vec4` | homogeneous / clip space | `perspective_divide`, `xyz` |
| `Mat3` | rotation, normal matrices | `multiply`, `transpose`, `determinant`, `transform_vector` |
| `Mat4` | model, view, projection | `translation`, `rotation_*`, `scaling`, `perspective`, `orthographic`, `multiply`, `transform_point` |
| `Quaternion` | rotation composition | `from_axis_angle`, `from_euler`, `rotate`, `slerp`, `to_mat3`, `to_mat4` |
| `Transform3D` | TRS triple | `matrix`, `normal_matrix`, `transform_point` |
| `Plane3`, `Frustum` | culling | `signed_distance`, `contains_point`, `intersects_sphere`, `from_matrix` |
| helpers | GPU-style transforms | `transform_vec4`, `transform_direction` |

## Conventions

* Row-major storage, column-vector maths: `v' = M v`.
* Right-handed world, camera looks down **-Z**, matching the projection matrix.
* `Mat4.perspective(fov, aspect, near, far)` maps `-near` to NDC `-1` and
  `-far` to `+1`; depth therefore increases with distance, so "smaller wins".
* Angles are degrees in the public API.

## Two transform types, on purpose

`py3dgame.Transform` (scene graph, Euler degrees, used by `Node`) and
`py3dgame.Transform3D` (quaternion maths, used by the renderer) both expose
`matrix()` and `normal_matrix()`, so `Renderer.draw` accepts either.

## Frustum

Planes are extracted from the combined view-projection matrix, so they are
already in world space and cost nothing per frame.
