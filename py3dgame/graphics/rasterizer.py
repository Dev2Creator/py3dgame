"""Triangle rasteriser: clipping, backface culling, depth test, interpolation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple

from ..math3d import Vec3, Vec4
from .framebuffer import ColorBuffer

ClipVertex = Dict[str, object]
ShadeFn = Callable[[Vec3, Vec3, Tuple[float, float]], Tuple[int, int, int, int]]

NEAR_EPSILON = 1e-6


@dataclass
class RenderStats:
    triangles_submitted: int = 0
    triangles_drawn: int = 0
    triangles_culled: int = 0
    triangles_clipped: int = 0
    fragments: int = 0
    draw_calls: int = 0

    def reset(self) -> None:
        self.triangles_submitted = 0
        self.triangles_drawn = 0
        self.triangles_culled = 0
        self.triangles_clipped = 0
        self.fragments = 0
        self.draw_calls = 0


def _interpolate(a: ClipVertex, b: ClipVertex, t: float) -> ClipVertex:
    def lerp4(u: Vec4, v: Vec4) -> Vec4:
        return Vec4(u.x + (v.x - u.x) * t, u.y + (v.y - u.y) * t,
                    u.z + (v.z - u.z) * t, u.w + (v.w - u.w) * t)

    world_a, world_b = a["world"], b["world"]
    normal_a, normal_b = a["normal"], b["normal"]
    uv_a, uv_b = a["uv"], b["uv"]
    return {
        "clip": lerp4(a["clip"], b["clip"]),
        "world": world_a + (world_b - world_a) * t,
        "normal": normal_a + (normal_b - normal_a) * t,
        "uv": (uv_a[0] + (uv_b[0] - uv_a[0]) * t, uv_a[1] + (uv_b[1] - uv_a[1]) * t),
    }


def clip_near(vertices: Sequence[ClipVertex]) -> List[ClipVertex]:
    """Sutherland-Hodgman clip against the near plane (z + w > 0)."""
    out: List[ClipVertex] = []
    count = len(vertices)
    for i in range(count):
        current = vertices[i]
        following = vertices[(i + 1) % count]
        d_current = current["clip"].z + current["clip"].w
        d_following = following["clip"].z + following["clip"].w
        inside_current = d_current > NEAR_EPSILON
        inside_following = d_following > NEAR_EPSILON
        if inside_current:
            out.append(current)
        if inside_current != inside_following:
            t = d_current / (d_current - d_following)
            out.append(_interpolate(current, following, t))
    return out


class Rasterizer:
    def __init__(self, target: ColorBuffer) -> None:
        self.target = target
        self.stats = RenderStats()

    def draw_triangle(self, a: ClipVertex, b: ClipVertex, c: ClipVertex,
                      shade_fn: ShadeFn, cull: bool = True) -> None:
        self.stats.triangles_submitted += 1
        polygon = clip_near((a, b, c))
        if len(polygon) < 3:
            self.stats.triangles_clipped += 1
            return
        for index in range(1, len(polygon) - 1):
            self._raster(polygon[0], polygon[index], polygon[index + 1], shade_fn, cull)

    def _raster(self, a: ClipVertex, b: ClipVertex, c: ClipVertex,
                shade_fn: ShadeFn, cull: bool) -> None:
        width, height = self.target.width, self.target.height
        screen = []
        depths = []
        inv_w = []
        for vertex in (a, b, c):
            clip: Vec4 = vertex["clip"]
            inverse = 1.0 / clip.w
            x = (clip.x * inverse * 0.5 + 0.5) * width
            y = (0.5 - clip.y * inverse * 0.5) * height
            screen.append((x, y))
            depths.append(clip.z * inverse)
            inv_w.append(inverse)

        (x0, y0), (x1, y1), (x2, y2) = screen
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if area == 0.0:
            return
        if cull and area >= 0.0:
            self.stats.triangles_culled += 1
            return

        min_x = max(0, int(math.floor(min(x0, x1, x2))))
        max_x = min(width - 1, int(math.ceil(max(x0, x1, x2))))
        min_y = max(0, int(math.floor(min(y0, y1, y2))))
        max_y = min(height - 1, int(math.ceil(max(y0, y1, y2))))
        if min_x > max_x or min_y > max_y:
            return

        inverse_area = 1.0 / area
        pixel = self.target.pixels
        depth_buffer = self.target.depth
        stride = width * 4
        vertices = (a, b, c)
        drew = False

        for py in range(min_y, max_y + 1):
            sample_y = py + 0.5
            row = py * width
            for px in range(min_x, max_x + 1):
                sample_x = px + 0.5
                w0 = ((x1 - sample_x) * (y2 - sample_y) - (x2 - sample_x) * (y1 - sample_y)) * inverse_area
                if w0 < 0.0:
                    continue
                w1 = ((x2 - sample_x) * (y0 - sample_y) - (x0 - sample_x) * (y2 - sample_y)) * inverse_area
                if w1 < 0.0:
                    continue
                w2 = 1.0 - w0 - w1
                if w2 < 0.0:
                    continue

                depth = w0 * depths[0] + w1 * depths[1] + w2 * depths[2]
                offset = row + px
                if depth >= depth_buffer[offset]:
                    continue

                reciprocal = w0 * inv_w[0] + w1 * inv_w[1] + w2 * inv_w[2]
                if reciprocal <= 0.0:
                    continue
                scale = 1.0 / reciprocal
                world = (vertices[0]["world"] * (w0 * inv_w[0])
                         + vertices[1]["world"] * (w1 * inv_w[1])
                         + vertices[2]["world"] * (w2 * inv_w[2])) * scale
                normal = (vertices[0]["normal"] * (w0 * inv_w[0])
                          + vertices[1]["normal"] * (w1 * inv_w[1])
                          + vertices[2]["normal"] * (w2 * inv_w[2])) * scale
                uv = ((vertices[0]["uv"][0] * w0 * inv_w[0]
                       + vertices[1]["uv"][0] * w1 * inv_w[1]
                       + vertices[2]["uv"][0] * w2 * inv_w[2]) * scale,
                      (vertices[0]["uv"][1] * w0 * inv_w[0]
                       + vertices[1]["uv"][1] * w1 * inv_w[1]
                       + vertices[2]["uv"][1] * w2 * inv_w[2]) * scale)

                colour = shade_fn(world, normal, uv)
                if colour[3] <= 0:
                    continue
                depth_buffer[offset] = depth
                pixel[offset * 4:offset * 4 + 4] = bytes((
                    max(0, min(255, colour[0])), max(0, min(255, colour[1])),
                    max(0, min(255, colour[2])), max(0, min(255, colour[3])),
                ))
                self.stats.fragments += 1
                drew = True

        if drew:
            self.stats.triangles_drawn += 1
