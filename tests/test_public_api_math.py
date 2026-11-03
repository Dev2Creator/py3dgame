"""Public API and maths: the contract a game developer codes against."""

from __future__ import annotations

import math

import pytest

import py3dgame as p3d


def test_public_surface_is_complete():
    for name in ("Game", "Scene", "Node", "Transform", "Vec2", "Vec3", "Mat4",
                 "Canvas", "InputState", "Window", "HeadlessWindow", "PygameWindow",
                 "create_window", "available_backends"):
        assert hasattr(p3d, name), f"missing public name {name}"


def test_version_is_exposed():
    assert p3d.__version__ == "0.4.0"


def test_exception_hierarchy():
    for exc in (p3d.ConfigurationError, p3d.BackendError, p3d.SceneError,
                p3d.AssetNotFoundError):
        assert issubclass(exc, p3d.Py3DGameError)
    assert issubclass(p3d.Py3DGameError, Exception)


def test_headless_backend_always_available():
    assert "headless" in p3d.available_backends()


def test_unknown_backend_is_rejected():
    with pytest.raises(p3d.ConfigurationError):
        p3d.create_window(backend="glfw")


def test_game_rejects_invalid_configuration():
    with pytest.raises(p3d.ConfigurationError):
        p3d.Game(fps=0, window="headless")
    with pytest.raises(p3d.ConfigurationError):
        p3d.Game(fixed_dt=0, window="headless")
    with pytest.raises(p3d.ConfigurationError):
        p3d.Game(max_substeps=0, window="headless")
    with pytest.raises(p3d.ConfigurationError):
        p3d.Game(width=0, window="headless")


# -- Vec2 / Vec3 ------------------------------------------------------- #

def test_vec2_arithmetic_and_normalisation():
    a, b = p3d.Vec2(3, 4), p3d.Vec2(1, 0)
    assert a.length() == pytest.approx(5.0)
    assert a + b == p3d.Vec2(4, 4)
    assert a - b == p3d.Vec2(2, 4)
    assert a * 2 == p3d.Vec2(6, 8)
    assert a.dot(b) == pytest.approx(3.0)
    assert a.normalized().length() == pytest.approx(1.0)
    assert tuple(a) == (3.0, 4.0)


def test_zero_length_vector_cannot_be_normalised():
    with pytest.raises(ValueError):
        p3d.Vec2(0, 0).normalized()
    with pytest.raises(ValueError):
        p3d.Vec3(0, 0, 0).normalized()


def test_vec3_cross_and_dot():
    x = p3d.Vec3(1, 0, 0)
    y = p3d.Vec3(0, 1, 0)
    assert x.cross(y) == p3d.Vec3(0, 0, 1)
    assert x.dot(y) == 0.0
    assert (x + y).length() == pytest.approx(math.sqrt(2))


# -- Mat4 -------------------------------------------------------------- #

def test_identity_and_translation_transform_points():
    point = p3d.Vec3(1, 2, 3)
    assert p3d.Mat4.identity().transform_point(point) == point
    moved = p3d.Mat4.translation(10, -1, 0.5).transform_point(point)
    assert moved == p3d.Vec3(11, 1, 3.5)


def test_matrix_multiplication_order():
    translate = p3d.Mat4.translation(5, 0, 0)
    scale = p3d.Mat4.scaling(2)
    # scale-then-translate keeps the translation unscaled
    assert (translate.multiply(scale)).transform_point(p3d.Vec3(1, 0, 0)) == p3d.Vec3(7, 0, 0)
    # translate-then-scale scales the translation too
    assert (scale.multiply(translate)).transform_point(p3d.Vec3(1, 0, 0)) == p3d.Vec3(12, 0, 0)


def test_rotation_z_turns_x_into_y():
    rotated = p3d.Mat4.rotation_z(90).transform_point(p3d.Vec3(1, 0, 0))
    assert rotated.x == pytest.approx(0, abs=1e-9)
    assert rotated.y == pytest.approx(1, abs=1e-9)


def test_perspective_matrix_matches_hand_calculation():
    m = p3d.Mat4.perspective(90, 1.0, 0.1, 100.0)
    assert m.m[0] == pytest.approx(1.0)          # 1 / tan(45deg)
    assert m.m[5] == pytest.approx(1.0)
    assert m.m[10] == pytest.approx(100.1 / -99.9)
    assert m.m[11] == pytest.approx(2 * 100 * 0.1 / -99.9)
    assert m.m[14] == pytest.approx(-1.0)


def test_perspective_maps_near_and_far_planes_to_minus_one_and_one():
    m = p3d.Mat4.perspective(90, 1.0, 0.1, 100.0)
    assert m.transform_point(p3d.Vec3(0, 0, -0.1)).z == pytest.approx(-1.0)
    assert m.transform_point(p3d.Vec3(0, 0, -100.0)).z == pytest.approx(1.0)


def test_perspective_divides_by_w():
    m = p3d.Mat4.perspective(90, 1.0, 0.1, 100.0)
    projected = m.transform_point(p3d.Vec3(1, 0, -2))
    assert -1.0 <= projected.z <= 1.0
    # x is divided by w (=2), so 1 unit at z=-2 lands at 0.5 in clip space
    assert projected.x == pytest.approx(0.5)


def test_projection_argument_validation():
    with pytest.raises(ValueError):
        p3d.Mat4.perspective(0, 1.0, 0.1, 10)
    with pytest.raises(ValueError):
        p3d.Mat4.perspective(60, 0, 0.1, 10)
    with pytest.raises(ValueError):
        p3d.Mat4.perspective(60, 1.0, 0, 10)
    with pytest.raises(ValueError):
        p3d.Mat4.perspective(60, 1.0, 10, 1)
    with pytest.raises(ValueError):
        p3d.Mat4.orthographic(0, 0, 0, 1, 0.1, 10)
    with pytest.raises(ValueError):
        p3d.Mat4([1, 2, 3])


def test_orthographic_projects_unit_cube():
    m = p3d.Mat4.orthographic(-1, 1, -1, 1, -1, 1)
    assert m.transform_point(p3d.Vec3(0, 0, 0)) == p3d.Vec3(0, 0, 0)
    corner = m.transform_point(p3d.Vec3(1, 1, 1))
    assert corner == p3d.Vec3(1, 1, -1)
