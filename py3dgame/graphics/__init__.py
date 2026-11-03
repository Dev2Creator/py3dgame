"""3D rendering: framebuffer, cameras, meshes, materials and the software renderer."""

from .camera import Camera, OrthographicCamera, PerspectiveCamera
from .framebuffer import ColorBuffer
from .material import SHADING_MODELS, Material
from .mesh import Mesh, Vertex
from .rasterizer import Rasterizer, RenderStats
from .renderer import Renderer, SoftwareRenderer

__all__ = [
    "Camera", "ColorBuffer", "Material", "Mesh", "OrthographicCamera",
    "PerspectiveCamera", "Rasterizer", "RenderStats", "Renderer",
    "SHADING_MODELS", "SoftwareRenderer", "Vertex",
]
