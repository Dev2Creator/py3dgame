"""3D graphics: cameras, meshes, materials, lights, rasteriser, renderer."""

from __future__ import annotations

import math

import pytest

from py3dgame.graphics import (
    Camera,
    ColorBuffer,
    Material,
    Mesh,
    OrthographicCamera,
    PerspectiveCamera,
    SoftwareRenderer,
    Vertex,
)
from py3dgame.lighting import DirectionalLight, PointLight, SpotLight, shade
from py3dgame.math3d import Vec3, Vec4, Transform, transform_vec4
from py3dgame.renderer2d.image import Image


def _camera(position=(2.6, 2.2, 3.4)):
    return PerspectiveCamera(55, 1.5, 0.5, 100, position=position).look_at(Vec3(0, 0, 0))


def test_perspective_projection_maps_near_plane_to_minus_one():
    camera = PerspectiveCamera(60, 1.0, 0.5, 100, position=(0, 0, 0)).look_at(Vec3(0, 0, -1))
    clip = transform_vec4(camera.projection_matrix(), Vec4(0, 0, -0.5, 1))
    assert clip.z / clip.w == pytest.approx(-1.0, abs=1e-9)
    far = transform_vec4(camera.projection_matrix(), Vec4(0, 0, -100, 1))
    assert far.z / far.w == pytest.approx(1.0, abs=1e-6)


def test_view_matrix_puts_target_in_front_of_camera():
    camera = _camera()
    view = transform_vec4(camera.view_matrix(), Vec4(0, 0, 0, 1))
    assert view.z < 0
    assert view.z == pytest.approx(-Vec3(2.6, 2.2, 3.4).length(), abs=1e-6)


def test_orthographic_projection_is_linear():
    camera = OrthographicCamera(height=4.0, aspect=1.0, near=0.5, far=10.0, position=(0, 0, 0))
    camera.look_at(Vec3(0, 0, -1))
    top = transform_vec4(camera.projection_matrix(), Vec4(0, 2, -1, 1))
    assert top.y / top.w == pytest.approx(1.0, abs=1e-9)
    assert top.x / top.w == pytest.approx(0.0, abs=1e-9)


def test_camera_validation():
    with pytest.raises(ValueError):
        PerspectiveCamera(fov_degrees=0)
    with pytest.raises(ValueError):
        PerspectiveCamera(fov_degrees=60, aspect=0)
    with pytest.raises(ValueError):
        Camera(position=(0, 0, 0), near=1.0, far=0.5)
    with pytest.raises(NotImplementedError):
        Camera().projection_matrix()


def test_mesh_builders_and_validation():
    cube = Mesh.cube(2.0)
    assert cube.vertex_count == 24
    assert cube.triangle_count == 12
    lower, upper = cube.bounds()
    assert lower == Vec3(-1, -1, -1)
    assert upper == Vec3(1, 1, 1)

    plane = Mesh.plane(4.0, 2)
    assert plane.vertex_count == 9
    assert plane.triangle_count == 8

    triangle = Mesh.triangle(1.0)
    assert triangle.triangle_count == 1

    with pytest.raises(ValueError):
        Mesh([Vertex(Vec3(0, 0, 0), Vec3(0, 0, 1))], (0, 1, 2))
    with pytest.raises(ValueError):
        Mesh([Vertex(Vec3(0, 0, 0), Vec3(0, 0, 1))], (0, 0))
    with pytest.raises(ValueError):
        Mesh.plane(1.0, 0)


def test_material_and_light_validation():
    assert Material(shading="pbr").metallic == 0.0
    with pytest.raises(ValueError):
        Material(shading="magic")
    with pytest.raises(ValueError):
        Material(metallic=2.0)
    with pytest.raises(ValueError):
        Material(roughness=-0.1)
    with pytest.raises(ValueError):
        Material(base_colour=(300, 0, 0))
    with pytest.raises(ValueError):
        DirectionalLight(direction=Vec3(0, 0, 0))
    with pytest.raises(ValueError):
        PointLight(reach=0)
    with pytest.raises(ValueError):
        SpotLight(inner_degrees=40, outer_degrees=20)


def test_lambert_is_darker_away_from_the_light():
    surface_normal = Vec3(0, 0, 1)
    view_position = Vec3(0, 0, 5)
    material = Material(base_colour=(200, 200, 200), shading="lambert")
    facing = shade(material, Vec3(0, 0, 0), surface_normal, view_position,
                   [DirectionalLight(direction=Vec3(0, 0, -1))])
    away = shade(material, Vec3(0, 0, 0), surface_normal, view_position,
                 [DirectionalLight(direction=Vec3(0, 0, 1))])
    assert sum(facing[:3]) > sum(away[:3])


def test_unlit_ignores_lighting_and_toon_quantises():
    material = Material(base_colour=(120, 40, 200), shading="unlit")
    dark = shade(material, Vec3(0, 0, 0), Vec3(0, 0, 1), Vec3(0, 0, 1), [])
    assert dark[:3] == (120, 40, 200)

    toon = Material(base_colour=(255, 255, 255), shading="toon")
    values = {
        shade(toon, Vec3(0, 0, 0), Vec3(0, 0, 1), Vec3(0, 0, 5),
              [DirectionalLight(direction=Vec3(0.2 * i - 0.5, -1, -1))])[:3]
        for i in range(12)
    }
    assert len(values) <= 4, "toon shading should quantise into a few bands"


def test_pbr_metallic_reduces_diffuse_response():
    material_dielectric = Material(base_colour=(200, 200, 200), shading="pbr", metallic=0.0, roughness=0.3)
    material_metal = Material(base_colour=(200, 200, 200), shading="pbr", metallic=1.0, roughness=0.3)
    lights = [DirectionalLight(direction=Vec3(0, -1, -1), intensity=2.0)]
    dielectric = shade(material_dielectric, Vec3(0, 0, 0), Vec3(0, 0, 1), Vec3(0, 0, 5), lights)
    metal = shade(material_metal, Vec3(0, 0, 0), Vec3(0, 0, 1), Vec3(0, 0, 5), lights)
    assert sum(dielectric[:3]) != sum(metal[:3])


def test_texture_sampling_drives_base_colour():
    texture = Image(2, 1)
    texture.set_pixel(0, 0, (255, 0, 0, 255))
    texture.set_pixel(1, 0, (0, 0, 255, 255))
    material = Material(shading="unlit", texture=texture)
    left = shade(material, Vec3(0, 0, 0), Vec3(0, 0, 1), Vec3(0, 0, 1), [], uv=(0.1, 0.5))
    right = shade(material, Vec3(0, 0, 0), Vec3(0, 0, 1), Vec3(0, 0, 1), [], uv=(0.9, 0.5))
    assert left[0] > left[2]
    assert right[2] > right[0]


def test_rasteriser_depth_test_prefers_the_nearer_surface():
    renderer = SoftwareRenderer(64, 64, PerspectiveCamera(60, 1.0, 0.5, 50, position=(0, 0, 0)).look_at(Vec3(0, 0, -1)))
    renderer.clear()
    near_triangle = Mesh.triangle(2.0)
    renderer.draw(near_triangle, Transform(position=(0, 0, -2)),
                  Material(base_colour=(255, 0, 0), shading="unlit"))
    renderer.draw(near_triangle, Transform(position=(0, 0, -6)),
                  Material(base_colour=(0, 255, 0), shading="unlit"))
    p = renderer.target.get_pixel(32, 20)
    assert p[0] > p[1], "the nearer red triangle must win the depth test"


def test_backface_culling_and_double_sided_material():
    camera = PerspectiveCamera(60, 1.0, 0.5, 50, position=(0, 0, 3)).look_at(Vec3(0, 0, 0))
    renderer = SoftwareRenderer(64, 64, camera)
    renderer.clear()
    renderer.draw(Mesh.triangle(1.0), None, Material(shading="unlit"))
    assert renderer.stats.triangles_drawn == 1

    renderer.clear()
    renderer.stats.reset()
    flipped = Transform(rotation=None)
    from py3dgame.math3d import Quaternion
    flipped.rotation = Quaternion.from_axis_angle(Vec3(0, 1, 0), 180)
    renderer.draw(Mesh.triangle(1.0), flipped, Material(shading="unlit"))
    assert renderer.stats.triangles_drawn == 0, "a back-facing triangle is culled"

    renderer.stats.reset()
    renderer.draw(Mesh.triangle(1.0), flipped, Material(shading="unlit", double_sided=True))
    assert renderer.stats.triangles_drawn == 1


def test_triangle_straddling_the_near_plane_is_clipped_not_dropped():
    camera = PerspectiveCamera(60, 1.0, 0.5, 50, position=(0, 0, 1))
    camera.look_at(Vec3(0, 0, -1))
    renderer = SoftwareRenderer(64, 64, camera)
    renderer.clear()
    # One vertex sits behind the camera, two are well in front.
    straddling = Mesh((
        Vertex(Vec3(0.0, 0.0, 1.5), Vec3(0, 0, 1)),
        Vertex(Vec3(-1.4, -0.9, -2.0), Vec3(0, 0, 1)),
        Vertex(Vec3(1.4, -0.9, -2.0), Vec3(0, 0, 1)),
    ), (0, 1, 2))
    renderer.draw(straddling, None, Material(shading="unlit", double_sided=True))
    assert renderer.stats.triangles_submitted == 1
    assert renderer.stats.fragments > 0, "the visible part of the triangle must still be drawn"


def test_renderer_culls_meshes_behind_the_camera():
    renderer = SoftwareRenderer(64, 64, _camera())
    renderer.clear()
    renderer.draw(Mesh.cube(1.0), Transform(position=(0, 0, 40)), Material())
    assert renderer.meshes_culled == 1
    assert renderer.stats.triangles_submitted == 0


def test_renderer_draws_a_cube_with_correct_counts_and_capabilities():
    renderer = SoftwareRenderer(160, 120, _camera())
    renderer.clear()
    renderer.draw(Mesh.cube(1.6), Transform(), Material(base_colour=(220, 150, 90)))
    assert renderer.stats.triangles_submitted == 12
    assert renderer.stats.triangles_drawn == 6
    assert renderer.stats.fragments > 500
    assert renderer.capabilities["gpu"] is False
    image = renderer.to_image()
    background = renderer.background
    painted = sum(1 for y in range(0, 120, 4) for x in range(0, 160, 4)
                  if image.get_pixel(x, y) != background)
    assert painted > 0


def test_renderer_rejects_bad_arguments():
    renderer = SoftwareRenderer(32, 32, _camera())
    with pytest.raises(TypeError):
        renderer.draw("not a mesh")
    with pytest.raises(ValueError):
        renderer.draw(Mesh.cube(1.0), Transform(), Material(), model_matrix=None.__class__)
    with pytest.raises(TypeError):
        renderer.draw(Mesh.cube(1.0), "transform")
