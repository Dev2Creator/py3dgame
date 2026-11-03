"""Damage, breakage states and radial destruction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from ..math3d import Vec2


@dataclass
class Destructible:
    name: str = "prop"
    health: float = 100.0
    position: Vec2 = field(default_factory=Vec2)
    debris_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.health <= 0:
            raise ValueError("health must be positive")
        if self.debris_scale < 0:
            raise ValueError("debris_scale must not be negative")
        if not isinstance(self.position, Vec2):
            self.position = Vec2(*self.position)
        self.max_health = self.health

    @property
    def ratio(self) -> float:
        return max(0.0, self.health / self.max_health)

    @property
    def state(self) -> str:
        ratio = self.ratio
        if ratio <= 0.0:
            return "destroyed"
        if ratio <= 0.33:
            return "critical"
        if ratio <= 0.66:
            return "damaged"
        return "intact"

    @property
    def debris(self) -> int:
        if self.state == "intact":
            return 0
        return int(round((1.0 - self.ratio) * 12 * self.debris_scale))

    def damage(self, amount: float) -> str:
        if amount < 0:
            raise ValueError("damage must not be negative")
        self.health = max(0.0, self.health - amount)
        return self.state

    def repair(self, amount: float) -> str:
        if amount < 0:
            raise ValueError("repair must not be negative")
        self.health = min(self.max_health, self.health + amount)
        return self.state


class DestructionSystem:
    def __init__(self) -> None:
        self.items: List[Destructible] = []

    def register(self, item: Destructible) -> Destructible:
        self.items.append(item)
        return item

    def damage_at(self, point: Vec2, radius: float, amount: float) -> List[Tuple[str, str]]:
        if radius <= 0:
            raise ValueError("radius must be positive")
        if amount < 0:
            raise ValueError("amount must not be negative")
        point = Vec2(*point) if not isinstance(point, Vec2) else point
        results: List[Tuple[str, str]] = []
        for item in self.items:
            distance = (item.position - point).length()
            if distance > radius:
                continue
            falloff = 1.0 - (distance / radius)
            results.append((item.name, item.damage(amount * falloff)))
        return results

    @property
    def destroyed(self) -> List[Destructible]:
        return [item for item in self.items if item.state == "destroyed"]

    def reset(self) -> None:
        for item in self.items:
            item.health = item.max_health
