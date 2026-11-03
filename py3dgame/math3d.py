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


# ---------------------------------------------------------------------------
# 3D extensions (0.4.0). Everything above stays exactly as it was.
# ---------------------------------------------------------------------------


class Vec4:
    """Homogeneous vector used for clip-space positions."""

    __slots__ = ("x", "y", "z", "w")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> None:
        self.x, self.y, self.z, self.w = float(x), float(y), float(z), float(w)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z
        yield self.w

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec4):
            return NotImplemented
        return (self.x, self.y, self.z, self.w) == (other.x, other.y, other.z, other.w)

    def __repr__(self) -> str:
        return f"Vec4({self.x:.4g}, {self.y:.4g}, {self.z:.4g}, {self.w:.4g})"

    def __add__(self, other: "Vec4") -> "Vec4":
        return Vec4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other: "Vec4") -> "Vec4":
        return Vec4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, scalar: float) -> "Vec4":
        return Vec4(self.x * scalar, self.y * scalar, self.z * scalar, self.w * scalar)

    __rmul__ = __mul__

    def dot(self, other: "Vec4") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def perspective_divide(self) -> "Vec3":
        if abs(self.w) < 1e-12:
            raise ZeroDivisionError("clip-space w is zero; the point is behind the eye")
        inverse = 1.0 / self.w
        return Vec3(self.x * inverse, self.y * inverse, self.z * inverse)

    def xyz(self) -> "Vec3":
        return Vec3(self.x, self.y, self.z)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.z, self.w)


class Mat3:
    """Row-major 3x3 matrix, used for normals and rotation without translation."""

    __slots__ = ("m",)

    def __init__(self, values: Iterable[float] | None = None) -> None:
        if values is None:
            self.m = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        else:
            values = tuple(float(v) for v in values)
            if len(values) != 9:
                raise ValueError("a Mat3 needs 9 values")
            self.m = values

    def __iter__(self) -> Iterator[float]:
        return iter(self.m)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mat3):
            return NotImplemented
        return self.m == other.m

    def __repr__(self) -> str:
        return f"Mat3({self.m!r})"

    @classmethod
    def identity(cls) -> "Mat3":
        return cls()

    @classmethod
    def from_quaternion(cls, quaternion: "Quaternion") -> "Mat3":
        x, y, z, w = quaternion.normalized().to_tuple_xyzw()
        return cls((
            1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y),
        ))

    def multiply(self, other: "Mat3") -> "Mat3":
        a, b = self.m, other.m
        return Mat3((
            a[0] * b[0] + a[1] * b[3] + a[2] * b[6],
            a[0] * b[1] + a[1] * b[4] + a[2] * b[7],
            a[0] * b[2] + a[1] * b[5] + a[2] * b[8],
            a[3] * b[0] + a[4] * b[3] + a[5] * b[6],
            a[3] * b[1] + a[4] * b[4] + a[5] * b[7],
            a[3] * b[2] + a[4] * b[5] + a[5] * b[8],
            a[6] * b[0] + a[7] * b[3] + a[8] * b[6],
            a[6] * b[1] + a[7] * b[4] + a[8] * b[7],
            a[6] * b[2] + a[7] * b[5] + a[8] * b[8],
        ))

    __matmul__ = multiply

    def transpose(self) -> "Mat3":
        a = self.m
        return Mat3((a[0], a[3], a[6], a[1], a[4], a[7], a[2], a[5], a[8]))

    def determinant(self) -> float:
        a = self.m
        return (
            a[0] * (a[4] * a[8] - a[5] * a[7])
            - a[1] * (a[3] * a[8] - a[5] * a[6])
            + a[2] * (a[3] * a[7] - a[4] * a[6])
        )

    def transform_vector(self, vector: Vec3) -> Vec3:
        a = self.m
        return Vec3(
            a[0] * vector.x + a[1] * vector.y + a[2] * vector.z,
            a[3] * vector.x + a[4] * vector.y + a[5] * vector.z,
            a[6] * vector.x + a[7] * vector.y + a[8] * vector.z,
        )

    def to_tuple(self) -> Tuple[float, ...]:
        return self.m


class Quaternion:
    """Unit quaternion stored as (x, y, z, w)."""

    __slots__ = ("x", "y", "z", "w")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0) -> None:
        self.x, self.y, self.z, self.w = float(x), float(y), float(z), float(w)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quaternion):
            return NotImplemented
        return (self.x, self.y, self.z, self.w) == (other.x, other.y, other.z, other.w)

    def __repr__(self) -> str:
        return f"Quaternion({self.x:.4g}, {self.y:.4g}, {self.z:.4g}, {self.w:.4g})"

    @classmethod
    def identity(cls) -> "Quaternion":
        return cls(0.0, 0.0, 0.0, 1.0)

    @classmethod
    def from_axis_angle(cls, axis: Vec3, degrees: float) -> "Quaternion":
        unit = axis.normalized()
        half = math.radians(degrees) * 0.5
        s = math.sin(half)
        return cls(unit.x * s, unit.y * s, unit.z * s, math.cos(half))

    @classmethod
    def from_euler(cls, x_degrees: float, y_degrees: float, z_degrees: float) -> "Quaternion":
        qx = cls.from_axis_angle(Vec3(1, 0, 0), x_degrees)
        qy = cls.from_axis_angle(Vec3(0, 1, 0), y_degrees)
        qz = cls.from_axis_angle(Vec3(0, 0, 1), z_degrees)
        return (qz * qy) * qx

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        if not isinstance(other, Quaternion):
            return NotImplemented
        return Quaternion(
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
        )

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)

    def normalized(self) -> "Quaternion":
        length = self.length()
        if length == 0.0:
            raise ValueError("cannot normalize a zero-length quaternion")
        inverse = 1.0 / length
        return Quaternion(self.x * inverse, self.y * inverse, self.z * inverse, self.w * inverse)

    def conjugate(self) -> "Quaternion":
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    def rotate(self, vector: Vec3) -> Vec3:
        q = self.normalized()
        v = Vec3(q.x, q.y, q.z)
        uv = v.cross(vector)
        uuv = v.cross(uv)
        return vector + (uv * (2.0 * q.w)) + (uuv * 2.0)

    def to_tuple_xyzw(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.z, self.w)

    def to_mat3(self) -> Mat3:
        return Mat3.from_quaternion(self)

    def to_mat4(self) -> "Mat4":
        r = self.to_mat3().m
        return Mat4((
            r[0], r[1], r[2], 0.0,
            r[3], r[4], r[5], 0.0,
            r[6], r[7], r[8], 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @staticmethod
    def slerp(a: "Quaternion", b: "Quaternion", t: float) -> "Quaternion":
        t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else float(t)
        cosom = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w
        if cosom < 0.0:
            b = Quaternion(-b.x, -b.y, -b.z, -b.w)
            cosom = -cosom
        if cosom > 0.9995:
            return Quaternion(
                a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t,
                a.z + (b.z - a.z) * t, a.w + (b.w - a.w) * t,
            ).normalized()
        omega = math.acos(cosom)
        sinom = math.sin(omega)
        scale_a = math.sin((1.0 - t) * omega) / sinom
        scale_b = math.sin(t * omega) / sinom
        return Quaternion(
            a.x * scale_a + b.x * scale_b, a.y * scale_a + b.y * scale_b,
            a.z * scale_a + b.z * scale_b, a.w * scale_a + b.w * scale_b,
        )


class Transform:
    """Position, rotation and scale, plus the matrix they compose."""

    __slots__ = ("position", "rotation", "scale")

    def __init__(self, position=None, rotation=None, scale=None) -> None:
        if isinstance(position, Vec3):
            self.position = position
        else:
            self.position = Vec3(*(position or (0.0, 0.0, 0.0)))
        self.rotation = rotation if isinstance(rotation, Quaternion) else Quaternion.identity()
        if isinstance(scale, Vec3):
            self.scale = scale
        elif scale is None:
            self.scale = Vec3(1.0, 1.0, 1.0)
        else:
            self.scale = Vec3(*scale)

    def __repr__(self) -> str:
        return f"Transform(position={self.position}, rotation={self.rotation}, scale={self.scale})"

    def matrix(self) -> "Mat4":
        translation = Mat4.translation(self.position.x, self.position.y, self.position.z)
        rotation = self.rotation.to_mat4()
        scaling = Mat4.scaling(self.scale.x, self.scale.y, self.scale.z)
        return translation.multiply(rotation).multiply(scaling)

    def normal_matrix(self) -> Mat3:
        return Mat3.from_quaternion(self.rotation)

    def transform_point(self, point: Vec3) -> Vec3:
        return self.matrix().transform_point(point)


class Plane3:
    """Plane in the form normal . p + d = 0, positive on the inside."""

    __slots__ = ("normal", "d")

    def __init__(self, normal: Vec3, d: float) -> None:
        self.normal = normal
        self.d = float(d)

    def __repr__(self) -> str:
        return f"Plane3(normal={self.normal}, d={self.d:.4g})"

    def normalized(self) -> "Plane3":
        length = self.normal.length()
        if length == 0.0:
            raise ValueError("cannot normalize a plane with a zero normal")
        return Plane3(self.normal * (1.0 / length), self.d / length)

    def signed_distance(self, point: Vec3) -> float:
        return self.normal.dot(point) + self.d


class Frustum:
    """The six clip planes extracted from a view-projection matrix."""

    __slots__ = ("planes",)

    def __init__(self, planes: Iterable[Plane3]) -> None:
        self.planes = tuple(planes)
        if len(self.planes) != 6:
            raise ValueError("a frustum needs exactly six planes")

    def __iter__(self) -> Iterator[Plane3]:
        return iter(self.planes)

    @classmethod
    def from_matrix(cls, matrix: "Mat4") -> "Frustum":
        m = matrix.m
        r0, r1, r2, r3 = m[0:4], m[4:8], m[8:12], m[12:16]

        def combine(a, b, sign: float) -> Plane3:
            return Plane3(
                Vec3(a[0] + sign * b[0], a[1] + sign * b[1], a[2] + sign * b[2]),
                a[3] + sign * b[3],
            ).normalized()

        return cls((
            combine(r3, r0, +1.0),
            combine(r3, r0, -1.0),
            combine(r3, r1, +1.0),
            combine(r3, r1, -1.0),
            combine(r3, r2, +1.0),
            combine(r3, r2, -1.0),
        ))

    def contains_point(self, point: Vec3) -> bool:
        return all(plane.signed_distance(point) >= 0.0 for plane in self.planes)

    def intersects_sphere(self, center: Vec3, radius: float) -> bool:
        if radius < 0.0:
            raise ValueError("a sphere radius cannot be negative")
        return all(plane.signed_distance(center) >= -radius for plane in self.planes)


def transform_vec4(matrix: Mat4, vector: Vec4) -> Vec4:
    """Apply a Mat4 to a homogeneous vector without dividing by w."""
    m = matrix.m
    x, y, z, w = vector.x, vector.y, vector.z, vector.w
    return Vec4(
        m[0] * x + m[1] * y + m[2] * z + m[3] * w,
        m[4] * x + m[5] * y + m[6] * z + m[7] * w,
        m[8] * x + m[9] * y + m[10] * z + m[11] * w,
        m[12] * x + m[13] * y + m[14] * z + m[15] * w,
    )


def transform_direction(matrix: Mat4, vector: Vec3) -> Vec3:
    """Apply the linear part of a Mat4, ignoring translation."""
    m = matrix.m
    return Vec3(
        m[0] * vector.x + m[1] * vector.y + m[2] * vector.z,
        m[4] * vector.x + m[5] * vector.y + m[6] * vector.z,
        m[8] * vector.x + m[9] * vector.y + m[10] * vector.z,
    )
