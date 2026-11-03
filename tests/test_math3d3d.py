"""3D maths: homogeneous vectors, matrices, quaternions, transforms, frustum."""

from __future__ import annotations

import math

import pytest

from py3dgame.math3d import (
    Frustum,
    Mat3,
    Mat4,
    Plane3,
    Quaternion,
    Transform,
    Vec3,
    Vec4,
    transform_direction,
    transform_vec4,
)


def test_vec4_basics_and_perspective_divide():
    v = Vec4(2.0, 4.0, 6.0, 2.0)
    assert v.xyz() == Vec3(2.0, 4.0, 6.0)
    assert v.perspective_divide() == Vec3(1.0, 2.0, 3.0)
    assert (v * 2.0).w == 4.0
    assert v.dot(Vec4(1, 1, 1, 1)) == 14.0
    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 0).perspective_divide()


def test_mat3_identity_transpose_determinant():
    identity = Mat3.identity()
    assert identity.transform_vector(Vec3(1, 2, 3)) == Vec3(1, 2, 3)
    assert identity.determinant() == pytest.approx(1.0)
    rotation = Quaternion.from_axis_angle(Vec3(0, 0, 1), 90).to_mat3()
    transposed = rotation.transpose()
    vector = Vec3(1, 0, 0)
    rotated = rotation.transform_vector(vector)
    back = transposed.transform_vector(rotated)
    assert back.x == pytest.approx(1.0, abs=1e-9)
    assert back.y == pytest.approx(0.0, abs=1e-9)
    assert rotation.determinant() == pytest.approx(1.0, abs=1e-9)


def test_mat3_multiply_matches_sequential_application():
    a = Quaternion.from_axis_angle(Vec3(0, 1, 0), 30).to_mat3()
    b = Quaternion.from_axis_angle(Vec3(1, 0, 0), 45).to_mat3()
    vector = Vec3(0.3, 0.7, -0.2)
    combined = a.multiply(b).transform_vector(vector)
    sequential = a.transform_vector(b.transform_vector(vector))
    assert combined.x == pytest.approx(sequential.x, abs=1e-9)
    assert combined.y == pytest.approx(sequential.y, abs=1e-9)
    assert combined.z == pytest.approx(sequential.z, abs=1e-9)


def test_quaternion_rotation_and_composition():
    quarter = Quaternion.from_axis_angle(Vec3(0, 0, 1), 90)
    rotated = quarter.rotate(Vec3(1, 0, 0))
    assert rotated.x == pytest.approx(0.0, abs=1e-9)
    assert rotated.y == pytest.approx(1.0, abs=1e-9)
    identity = quarter * quarter.conjugate()
    assert identity.w == pytest.approx(1.0, abs=1e-9)
    euler = Quaternion.from_euler(0, 90, 0)
    assert euler.rotate(Vec3(1, 0, 0)).z == pytest.approx(-1.0, abs=1e-9)


def test_quaternion_slerp_and_validation():
    a = Quaternion.identity()
    b = Quaternion.from_axis_angle(Vec3(0, 1, 0), 90)
    middle = Quaternion.slerp(a, b, 0.5)
    angle = 2 * math.degrees(math.acos(max(-1.0, min(1.0, middle.w))))
    assert angle == pytest.approx(45.0, abs=1e-6)
    assert Quaternion.slerp(a, b, -5.0).w == pytest.approx(1.0)
    with pytest.raises(ValueError):
        Quaternion(0, 0, 0, 0).normalized()


def test_transform_composes_translation_rotation_scale():
    transform = Transform(position=(1, 2, 3), rotation=Quaternion.from_axis_angle(Vec3(0, 1, 0), 90),
                          scale=Vec3(2, 2, 2))
    result = transform.transform_point(Vec3(1, 0, 0))
    assert result.x == pytest.approx(1.0, abs=1e-9)
    assert result.y == pytest.approx(2.0, abs=1e-9)
    assert result.z == pytest.approx(1.0, abs=1e-9)
    assert transform.normal_matrix().transform_vector(Vec3(0, 0, 1)).x == pytest.approx(1.0, abs=1e-9)


def test_frustum_accepts_inside_and_rejects_behind():
    frustum = Frustum.from_matrix(Mat4.perspective(60, 1.6, 0.5, 100))
    assert frustum.contains_point(Vec3(0, 0, -10))
    assert not frustum.contains_point(Vec3(0, 0, 10))
    assert frustum.intersects_sphere(Vec3(0, 0, -10), 2.0)
    assert not frustum.intersects_sphere(Vec3(0, 0, 10), 2.0)
    with pytest.raises(ValueError):
        frustum.intersects_sphere(Vec3(0, 0, -1), -1.0)


def test_plane_signed_distance_and_normalisation():
    plane = Plane3(Vec3(0, 2, 0), -4).normalized()
    assert plane.signed_distance(Vec3(0, 3, 0)) == pytest.approx(1.0)
    assert plane.signed_distance(Vec3(0, 1, 0)) == pytest.approx(-1.0)
    with pytest.raises(ValueError):
        Plane3(Vec3(0, 0, 0), 0).normalized()


def test_transform_helpers_match_matrix_path():
    matrix = Mat4.translation(1, 2, 3)
    vector = Vec4(1, 1, 1, 1)
    assert transform_vec4(matrix, vector) == Vec4(2, 3, 4, 1)
    assert transform_direction(matrix, Vec3(1, 1, 1)) == Vec3(1, 1, 1)
