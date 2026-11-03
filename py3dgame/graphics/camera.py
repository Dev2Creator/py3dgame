"""Perspective and orthographic cameras built on the 3D maths layer."""

from __future__ import annotations

import math

from ..math3d import Frustum, Mat3, Mat4, Quaternion, Vec3


def _quaternion_from_mat3(matrix: Mat3) -> Quaternion:
    m = matrix.m
    trace = m[0] + m[4] + m[8]
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        return Quaternion((m[7] - m[5]) / s, (m[2] - m[6]) / s, (m[3] - m[1]) / s, 0.25 * s).normalized()
    if m[0] > m[4] and m[0] > m[8]:
        s = math.sqrt(1.0 + m[0] - m[4] - m[8]) * 2.0
        return Quaternion(0.25 * s, (m[1] + m[3]) / s, (m[2] + m[6]) / s, (m[7] - m[5]) / s).normalized()
    if m[4] > m[8]:
        s = math.sqrt(1.0 + m[4] - m[0] - m[8]) * 2.0
        return Quaternion((m[1] + m[3]) / s, 0.25 * s, (m[5] + m[7]) / s, (m[2] - m[6]) / s).normalized()
    s = math.sqrt(1.0 + m[8] - m[0] - m[4]) * 2.0
    return Quaternion((m[2] + m[6]) / s, (m[5] + m[7]) / s, 0.25 * s, (m[3] - m[1]) / s).normalized()


class Camera:
    """Base camera: a pose plus a projection."""

    def __init__(self, position=(0.0, 1.5, 4.0), near: float = 0.1, far: float = 200.0) -> None:
        if near <= 0.0 or far <= near:
            raise ValueError("camera needs 0 < near < far")
        self.position = position if isinstance(position, Vec3) else Vec3(*position)
        self.rotation = Quaternion.identity()
        self.near = float(near)
        self.far = float(far)

    def look_at(self, target: Vec3, up: Vec3 | None = None) -> "Camera":
        up = up if isinstance(up, Vec3) else Vec3(0.0, 1.0, 0.0)
        forward = (target - self.position).normalized()
        if abs(forward.dot(up.normalized())) > 0.999:
            up = Vec3(0.0, 0.0, 1.0)
        right = forward.cross(up).normalized()
        true_up = right.cross(forward)
        basis = Mat3((
            right.x, true_up.x, -forward.x,
            right.y, true_up.y, -forward.y,
            right.z, true_up.z, -forward.z,
        ))
        self.rotation = _quaternion_from_mat3(basis)
        return self

    def view_matrix(self) -> Mat4:
        inverse_rotation = self.rotation.conjugate().to_mat4()
        inverse_translation = Mat4.translation(-self.position.x, -self.position.y, -self.position.z)
        return inverse_rotation.multiply(inverse_translation)

    def projection_matrix(self) -> Mat4:
        raise NotImplementedError

    def view_projection(self) -> Mat4:
        return self.projection_matrix().multiply(self.view_matrix())

    def frustum(self) -> Frustum:
        return Frustum.from_matrix(self.view_projection())


class PerspectiveCamera(Camera):
    def __init__(self, fov_degrees: float = 60.0, aspect: float = 16.0 / 9.0,
                 near: float = 0.1, far: float = 200.0, position=(0.0, 1.5, 4.0)) -> None:
        super().__init__(position, near, far)
        if not 0.0 < fov_degrees < 180.0:
            raise ValueError("field of view must be between 0 and 180 degrees")
        if aspect <= 0.0:
            raise ValueError("aspect ratio must be positive")
        self.fov_degrees = float(fov_degrees)
        self.aspect = float(aspect)

    def projection_matrix(self) -> Mat4:
        return Mat4.perspective(self.fov_degrees, self.aspect, self.near, self.far)


class OrthographicCamera(Camera):
    def __init__(self, height: float = 4.0, aspect: float = 16.0 / 9.0,
                 near: float = 0.1, far: float = 200.0, position=(0.0, 0.0, 4.0)) -> None:
        super().__init__(position, near, far)
        if height <= 0.0:
            raise ValueError("orthographic height must be positive")
        if aspect <= 0.0:
            raise ValueError("aspect ratio must be positive")
        self.height = float(height)
        self.aspect = float(aspect)

    def projection_matrix(self) -> Mat4:
        half_h = self.height * 0.5
        half_w = half_h * self.aspect
        return Mat4.orthographic(-half_w, half_w, -half_h, half_h, self.near, self.far)
