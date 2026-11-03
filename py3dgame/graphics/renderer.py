"""Backend-independent renderer with a software implementation.

The software backend is a correctness reference. It rasterises on the CPU and is
honest about it: `capabilities` reports exactly what this backend does, so a
future OpenGL or Vulkan backend can be dropped in without pretending the CPU
path is hardware accelerated.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..lighting.light import DirectionalLight
from ..lighting.shading import shade
from ..math3d import Mat3, Mat4, Transform, Vec3, Vec4, transform_vec4
from .camera import Camera, PerspectiveCamera
from .framebuffer import ColorBuffer
from .material import Material
from .mesh import Mesh
from .rasterizer import Rasterizer, RenderStats


class Renderer:
    """Interface every rendering backend implements."""

    backend_name = "abstract"
    capabilities: Dict[str, bool] = {}

    def draw(self, mesh: Mesh, transform=None, material: Optional[Material] = None,
             model_matrix: Optional[Mat4] = None) -> None:
        raise NotImplementedError


class SoftwareRenderer(Renderer):
    backend_name = "software"
    capabilities = {
        "depth_test": True,
        "textures": True,
        "per_pixel_lighting": True,
        "shadow_maps": False,
        "instancing": False,
        "msaa": False,
        "gpu": False,
    }

    def __init__(self, width: int = 320, height: int = 180,
                 camera: Optional[Camera] = None,
                 background: Tuple[int, int, int, int] = (16, 18, 26, 255)) -> None:
        self.width = int(width)
        self.height = int(height)
        self.target = ColorBuffer(self.width, self.height)
        self.camera = camera or PerspectiveCamera(aspect=self.width / self.height,
                                                  position=(2.4, 1.9, 3.4))
        self.lights: List[object] = [DirectionalLight()]
        self.ambient: Sequence[float] = (0.16, 0.18, 0.24)
        self.background = tuple(background)
        self.rasterizer = Rasterizer(self.target)
        self.stats = self.rasterizer.stats
        self.meshes_culled = 0
        self.target.clear(self.background)

    @property
    def stats_snapshot(self) -> RenderStats:
        return self.stats

    def clear(self, colour: Optional[Tuple[int, int, int, int]] = None) -> None:
        self.target.clear(colour or self.background)

    def draw(self, mesh: Mesh, transform=None, material: Optional[Material] = None,
             model_matrix: Optional[Mat4] = None) -> None:
        if not isinstance(mesh, Mesh):
            raise TypeError("draw() expects a Mesh")
        if transform is not None and model_matrix is not None:
            raise ValueError("pass either transform or model_matrix, not both")
        material = material or Material()
        if model_matrix is not None:
            model = model_matrix
            normal_matrix = Mat3.identity()
            scale = 1.0
        elif transform is not None:
            # Both math3d.Transform3D and the scene-graph Transform expose these.
            if not (hasattr(transform, "matrix") and hasattr(transform, "normal_matrix")):
                raise TypeError("transform must provide matrix() and normal_matrix()")
            model = transform.matrix()
            normal_matrix = transform.normal_matrix()
            scale_axis = getattr(transform, "scale", None)
            scale = max(abs(scale_axis.x), abs(scale_axis.y), abs(scale_axis.z)) if scale_axis else 1.0
        else:
            model = Mat4.identity()
            normal_matrix = Mat3.identity()
            scale = 1.0

        lower, upper = mesh.bounds()
        centre = (lower + upper) * 0.5
        radius = (upper - lower).length() * 0.5 * max(scale, 1e-6)
        world_centre = model.transform_point(centre)
        if not self.camera.frustum().intersects_sphere(world_centre, radius):
            self.meshes_culled += 1
            return

        mvp = self.camera.view_projection().multiply(model)
        camera_position = self.camera.position
        lights = self.lights
        ambient = self.ambient
        cull = not material.double_sided

        def shade_fn(world: Vec3, normal: Vec3, uv: Tuple[float, float]):
            world_normal = normal_matrix.transform_vector(normal)
            return shade(material, world, world_normal, camera_position, lights, uv, ambient)

        self.stats.draw_calls += 1
        for v0, v1, v2 in mesh.triangles():
            triangle = tuple(
                {
                    "clip": transform_vec4(mvp, Vec4(v.position.x, v.position.y, v.position.z, 1.0)),
                    "world": model.transform_point(v.position),
                    "normal": v.normal,
                    "uv": v.uv,
                }
                for v in (v0, v1, v2)
            )
            self.rasterizer.draw_triangle(triangle[0], triangle[1], triangle[2], shade_fn, cull)

    def to_image(self):
        return self.target.to_image()

    def save_png(self, path) -> None:
        self.to_image().save(path)
