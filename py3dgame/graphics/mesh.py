"""Indexed triangle meshes with positions, normals and texture coordinates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from ..math3d import Vec3


@dataclass(frozen=True)
class Vertex:
    position: Vec3
    normal: Vec3
    uv: Tuple[float, float] = (0.0, 0.0)


class Mesh:
    """Vertex and index buffers that the rasteriser can consume."""

    __slots__ = ("name", "vertices", "indices")

    def __init__(self, vertices: Sequence[Vertex], indices: Sequence[int], name: str = "mesh") -> None:
        if len(indices) < 3:
            raise ValueError("a mesh needs at least one triangle")
        if len(indices) % 3 != 0:
            raise ValueError("indices must come in triangles")
        count = len(vertices)
        for index in indices:
            if not isinstance(index, int):
                raise TypeError("indices must be integers")
            if not 0 <= index < count:
                raise ValueError(f"index {index} is outside the vertex buffer ({count} vertices)")
        if count == 0:
            raise ValueError("a mesh needs vertices")
        self.name = str(name)
        self.vertices = tuple(vertices)
        self.indices = tuple(indices)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def triangle_count(self) -> int:
        return len(self.indices) // 3

    def triangles(self):
        v = self.vertices
        for i in range(0, len(self.indices), 3):
            yield v[self.indices[i]], v[self.indices[i + 1]], v[self.indices[i + 2]]

    def bounds(self) -> Tuple[Vec3, Vec3]:
        xs = [v.position.x for v in self.vertices]
        ys = [v.position.y for v in self.vertices]
        zs = [v.position.z for v in self.vertices]
        return Vec3(min(xs), min(ys), min(zs)), Vec3(max(xs), max(ys), max(zs))

    def __repr__(self) -> str:
        return f"Mesh({self.name!r}, vertices={self.vertex_count}, triangles={self.triangle_count})"

    @classmethod
    def triangle(cls, size: float = 1.0) -> "Mesh":
        h = size * 0.5
        normal = Vec3(0.0, 0.0, 1.0)
        vertices = (
            Vertex(Vec3(-h, -h, 0.0), normal, (0.0, 0.0)),
            Vertex(Vec3(h, -h, 0.0), normal, (1.0, 0.0)),
            Vertex(Vec3(0.0, h, 0.0), normal, (0.5, 1.0)),
        )
        return cls(vertices, (0, 1, 2), name="triangle")

    @classmethod
    def plane(cls, size: float = 1.0, subdivisions: int = 1) -> "Mesh":
        if subdivisions < 1:
            raise ValueError("subdivisions must be at least 1")
        half = size * 0.5
        step = size / subdivisions
        vertices: List[Vertex] = []
        normal = Vec3(0.0, 1.0, 0.0)
        for row in range(subdivisions + 1):
            for column in range(subdivisions + 1):
                x = -half + column * step
                z = -half + row * step
                vertices.append(Vertex(Vec3(x, 0.0, z), normal,
                                       (column / subdivisions, row / subdivisions)))
        indices: List[int] = []
        stride = subdivisions + 1
        for row in range(subdivisions):
            for column in range(subdivisions):
                a = row * stride + column
                b = a + 1
                c = a + stride
                d = c + 1
                indices.extend((a, c, b, b, c, d))
        return cls(vertices, indices, name="plane")

    @classmethod
    def cube(cls, size: float = 1.0) -> "Mesh":
        h = size * 0.5
        faces = (
            (Vec3(1, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1)),
            (Vec3(-1, 0, 0), Vec3(0, 0, 1), Vec3(0, 1, 0)),
            (Vec3(0, 1, 0), Vec3(0, 0, 1), Vec3(1, 0, 0)),
            (Vec3(0, -1, 0), Vec3(1, 0, 0), Vec3(0, 0, 1)),
            (Vec3(0, 0, 1), Vec3(1, 0, 0), Vec3(0, 1, 0)),
            (Vec3(0, 0, -1), Vec3(0, 1, 0), Vec3(1, 0, 0)),
        )
        vertices: List[Vertex] = []
        indices: List[int] = []
        uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        for normal, u_axis, v_axis in faces:
            base = len(vertices)
            centre = normal * h
            for sign_u, sign_v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                position = centre + u_axis * (sign_u * h) + v_axis * (sign_v * h)
                vertices.append(Vertex(position, normal, uvs[((sign_u + 1) // 2) + ((sign_v + 1) // 2) * 2]))
            indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))
        return cls(vertices, indices, name="cube")
