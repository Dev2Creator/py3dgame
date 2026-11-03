"""Scene graph: transforms, nodes and scenes.

World transforms are composed parent-first, so a child's ``world_matrix()`` is
``parent.world_matrix() * local``. This is the foundation the 3D renderer and
physics backends will consume, so it is covered by tests now.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional

from ..exceptions import SceneError
from ..math3d import Mat4, Vec3

__all__ = ["Transform", "Node", "Scene"]

UpdateHook = Callable[[float], None]


@dataclass
class Transform:
    """Local position, Euler rotation in degrees, and scale."""

    position: Vec3 = field(default_factory=Vec3)
    rotation: Vec3 = field(default_factory=Vec3)
    scale: Vec3 = field(default_factory=lambda: Vec3(1.0, 1.0, 1.0))

    def __post_init__(self) -> None:
        """Accept plain tuples as well as Vec3 so transforms stay easy to write."""
        for name, default in (("position", (0.0, 0.0, 0.0)), ("rotation", (0.0, 0.0, 0.0)),
                              ("scale", (1.0, 1.0, 1.0))):
            value = getattr(self, name, None)
            if isinstance(value, Vec3):
                continue
            if value is None:
                setattr(self, name, Vec3(*default))
                continue
            try:
                setattr(self, name, Vec3(*value))
            except TypeError as exc:
                raise TypeError(
                    f"{name} accepts a Vec3 or a 3-item sequence, not {type(value).__name__}; "
                    "use py3dgame.Transform3D for quaternion rotations"
                ) from exc

    def local_matrix(self) -> Mat4:
        translate = Mat4.translation(self.position.x, self.position.y, self.position.z)
        rotate = (
            Mat4.rotation_z(self.rotation.z)
            .multiply(Mat4.rotation_y(self.rotation.y))
            .multiply(Mat4.rotation_x(self.rotation.x))
        )
        scale = Mat4.scaling(self.scale.x, self.scale.y, self.scale.z)
        return translate.multiply(rotate).multiply(scale)


    def matrix(self) -> Mat4:
        """Compose position, Euler rotation and scale into a model matrix."""
        from ..math3d import Mat4

        translation = Mat4.translation(self.position.x, self.position.y, self.position.z)
        rotation = (Mat4.rotation_z(self.rotation.z)
                    .multiply(Mat4.rotation_y(self.rotation.y))
                    .multiply(Mat4.rotation_x(self.rotation.x)))
        scaling = Mat4.scaling(self.scale.x, self.scale.y, self.scale.z)
        return translation.multiply(rotation).multiply(scaling)

    def normal_matrix(self):
        from ..math3d import Mat3, Quaternion

        rotation = Quaternion.from_euler(self.rotation.x, self.rotation.y, self.rotation.z)
        return Mat3.from_quaternion(rotation)


class Node:
    """A named object in the scene graph."""

    def __init__(self, name: str = "node", position: Optional[Vec3] = None) -> None:
        if not isinstance(name, str) or not name.strip():
            raise SceneError("node name must be a non-empty string")
        self.name = name
        self.transform = Transform()
        if position is not None:
            if not isinstance(position, Vec3):
                raise SceneError("position must be a Vec3")
            self.transform.position = position
        self.children: List["Node"] = []
        self.parent: Optional["Node"] = None
        self.visible: bool = True
        self.on_update: Optional[UpdateHook] = None

    # -- hierarchy --------------------------------------------------- #
    def add(self, child: "Node") -> "Node":
        if not isinstance(child, Node):
            raise SceneError("only Node instances can be added to a node")
        if child is self:
            raise SceneError("a node cannot be added to itself")
        if child.contains(self):
            raise SceneError(f"adding '{child.name}' under '{self.name}' would create a cycle")
        if child.parent is not None and child.parent is not self:
            child.parent.remove(child)
        if child.parent is None:
            child.parent = self
            self.children.append(child)
        return child

    def remove(self, child: "Node") -> bool:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            return True
        return False

    def detach(self) -> None:
        if self.parent is not None:
            self.parent.remove(self)

    def contains(self, node: "Node") -> bool:
        return any(candidate is node for candidate in self.walk())

    def walk(self) -> Iterator["Node"]:
        yield self
        for child in self.children:
            yield from child.walk()

    def find(self, name: str) -> Optional["Node"]:
        return next((node for node in self.walk() if node.name == name), None)

    # -- transforms -------------------------------------------------- #
    def world_matrix(self) -> Mat4:
        local = self.transform.local_matrix()
        if self.parent is None:
            return local
        return self.parent.world_matrix().multiply(local)

    def world_position(self) -> Vec3:
        m = self.world_matrix().m
        return Vec3(m[3], m[7], m[11])

    # -- lifecycle --------------------------------------------------- #
    def update(self, dt: float) -> None:
        if self.on_update is not None:
            self.on_update(dt)
        for child in list(self.children):
            child.update(dt)

    def __repr__(self) -> str:
        return f"Node(name={self.name!r}, children={len(self.children)})"


class Scene:
    """A named collection of nodes with a background colour."""

    def __init__(self, name: str = "Scene") -> None:
        if not isinstance(name, str) or not name.strip():
            raise SceneError("scene name must be a non-empty string")
        self.name = name
        self.root = Node(name)
        self.background = (12, 12, 16, 255)

    def add(self, node: Node) -> Node:
        return self.root.add(node)

    # Explicit aliases so call sites read naturally without duplicating logic.
    add_node = add

    def remove(self, node: Node) -> bool:
        return self.root.remove(node)

    remove_node = remove

    def find(self, name: str) -> Optional[Node]:
        return self.root.find(name)

    def walk(self) -> Iterator[Node]:
        return self.root.walk()

    def update(self, dt: float) -> None:
        self.root.update(dt)

    @property
    def nodes(self) -> List[Node]:
        return list(self.root.children)

    def node_count(self) -> int:
        return sum(1 for _ in self.walk()) - 1  # exclude the root

    def __iter__(self) -> Iterator[Node]:
        return self.walk()

    def __repr__(self) -> str:
        return f"Scene(name={self.name!r}, nodes={self.node_count()})"
