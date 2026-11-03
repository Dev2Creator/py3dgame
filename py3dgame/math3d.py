"""Vector and matrix maths for the engine (pure Python, no native dependency).

Column-vector convention: points are transformed as ``M * v``. Matrices are
stored row-major as a 16-tuple, which is the order used by ``to_tuple`` and by
the tests that pin the perspective and orthographic forms.
"""

from __future__ import annotations

import math
from typing import Iterable, Iterator, Tuple

__all__ = ["Vec2", "Vec3", "Mat4"]

_EPS = 1e-9


class Vec2:
    """Two-component vector used by 2D games and screen-space maths."""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec2):
            return NotImplemented
        return abs(self.x - other.x) < _EPS and abs(self.y - other.y) < _EPS

    def __hash__(self) -> int:
        return hash((round(self.x, 9), round(self.y, 9)))

    def __repr__(self) -> str:
        return f"Vec2({self.x:g}, {self.y:g})"

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length_squared(self) -> float:
        return self.dot(self)

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def normalized(self) -> "Vec2":
        length = self.length()
        if length < _EPS:
            raise ValueError("cannot normalize a zero-length Vec2")
        return Vec2(self.x / length, self.y / length)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


class Vec3:
    """Three-component vector for world space, colours and directions."""

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec3):
            return NotImplemented
        return (
            abs(self.x - other.x) < _EPS
            and abs(self.y - other.y) < _EPS
            and abs(self.z - other.z) < _EPS
        )

    def __hash__(self) -> int:
        return hash((round(self.x, 9), round(self.y, 9), round(self.z, 9)))

    def __repr__(self) -> str:
        return f"Vec3({self.x:g}, {self.y:g}, {self.z:g})"

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length_squared(self) -> float:
        return self.dot(self)

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def normalized(self) -> "Vec3":
        length = self.length()
        if length < _EPS:
            raise ValueError("cannot normalize a zero-length Vec3")
        return Vec3(self.x / length, self.y / length, self.z / length)

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


class Mat4:
    """4x4 matrix, row-major, used for transforms and projection."""

    __slots__ = ("m",)

    IDENTITY: Tuple[float, ...] = (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )

    def __init__(self, values: Iterable[float] | None = None) -> None:
        if values is None:
            self.m = self.IDENTITY
            return
        entries = tuple(float(v) for v in values)
        if len(entries) != 16:
            raise ValueError(f"Mat4 needs 16 values, got {len(entries)}")
        self.m = entries

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mat4):
            return NotImplemented
        return all(abs(a - b) < 1e-9 for a, b in zip(self.m, other.m))

    def __repr__(self) -> str:
        rows = [self.m[i * 4:(i + 1) * 4] for i in range(4)]
        body = "; ".join(", ".join(f"{v:g}" for v in row) for row in rows)
        return f"Mat4({body})"

    def to_tuple(self) -> Tuple[float, ...]:
        return self.m

    @classmethod
    def identity(cls) -> "Mat4":
        return cls()

    @classmethod
    def translation(cls, x: float, y: float, z: float) -> "Mat4":
        return cls((
            1.0, 0.0, 0.0, float(x),
            0.0, 1.0, 0.0, float(y),
            0.0, 0.0, 1.0, float(z),
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def scaling(cls, x: float, y: float | None = None, z: float | None = None) -> "Mat4":
        sy = float(x) if y is None else float(y)
        sz = float(x) if z is None else float(z)
        return cls((
            float(x), 0.0, 0.0, 0.0,
            0.0, sy, 0.0, 0.0,
            0.0, 0.0, sz, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation_x(cls, degrees: float) -> "Mat4":
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        return cls((
            1.0, 0.0, 0.0, 0.0,
            0.0, c, -s, 0.0,
            0.0, s, c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation_y(cls, degrees: float) -> "Mat4":
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        return cls((
            c, 0.0, s, 0.0,
            0.0, 1.0, 0.0, 0.0,
            -s, 0.0, c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation_z(cls, degrees: float) -> "Mat4":
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        return cls((
            c, -s, 0.0, 0.0,
            s, c, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def perspective(cls, fov_degrees: float, aspect: float, near: float, far: float) -> "Mat4":
        """Right-handed perspective projection with a -1..1 depth range."""
        if not 0.0 < fov_degrees < 180.0:
            raise ValueError("fov_degrees must be between 0 and 180")
        if aspect <= 0:
            raise ValueError("aspect must be positive")
        if near <= 0:
            raise ValueError("near must be positive")
        if far <= near:
            raise ValueError("far must be greater than near")
        f = 1.0 / math.tan(math.radians(fov_degrees) / 2.0)
        return cls((
            f / aspect, 0.0, 0.0, 0.0,
            0.0, f, 0.0, 0.0,
            0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far),
            0.0, 0.0, -1.0, 0.0,
        ))

    @classmethod
    def orthographic(cls, left: float, right: float, bottom: float, top: float,
                     near: float, far: float) -> "Mat4":
        if right == left or top == bottom or far == near:
            raise ValueError("orthographic bounds must not be degenerate")
        return cls((
            2.0 / (right - left), 0.0, 0.0, -(right + left) / (right - left),
            0.0, 2.0 / (top - bottom), 0.0, -(top + bottom) / (top - bottom),
            0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near),
            0.0, 0.0, 0.0, 1.0,
        ))

    def multiply(self, other: "Mat4") -> "Mat4":
        a, b = self.m, other.m
        out = [0.0] * 16
        for row in range(4):
            for col in range(4):
                out[row * 4 + col] = sum(a[row * 4 + k] * b[k * 4 + col] for k in range(4))
        return Mat4(out)

    def __matmul__(self, other: "Mat4") -> "Mat4":
        return self.multiply(other)

    def transform_point(self, point: Vec3) -> Vec3:
        x, y, z = point.x, point.y, point.z
        m = self.m
        rx = m[0] * x + m[1] * y + m[2] * z + m[3]
        ry = m[4] * x + m[5] * y + m[6] * z + m[7]
        rz = m[8] * x + m[9] * y + m[10] * z + m[11]
        rw = m[12] * x + m[13] * y + m[14] * z + m[15]
        if abs(rw) > _EPS and abs(rw - 1.0) > _EPS:
            return Vec3(rx / rw, ry / rw, rz / rw)
        return Vec3(rx, ry, rz)
