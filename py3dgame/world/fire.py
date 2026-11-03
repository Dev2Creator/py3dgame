"""Grid fire propagation with wind and moisture, in the spirit of Dunia's fire.

A cellular automaton: burning cells consume fuel, dry neighbours catch with a
probability biased downwind. Deterministic for a given seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

from ..math3d import Vec2

UNBURNT, BURNING, BURNT = 0, 1, 2


@dataclass(frozen=True)
class FireStats:
    burning: int
    burnt: int
    unburnt: int
    spread_events: int


class FireGrid:
    def __init__(
        self,
        width: int,
        height: int,
        moisture: float = 0.15,
        wind: Tuple[float, float] = (0.6, 0.0),
        spread_rate: float = 0.9,
        burn_rate: float = 0.35,
        seed: int = 1337,
    ):
        if width <= 0 or height <= 0:
            raise ValueError("fire grid needs positive dimensions")
        if not 0.0 <= moisture <= 1.0:
            raise ValueError("moisture must be within 0..1")
        if spread_rate < 0 or burn_rate <= 0:
            raise ValueError("spread_rate must be >= 0 and burn_rate > 0")
        self.width = int(width)
        self.height = int(height)
        self.moisture = float(moisture)
        self.wind = Vec2(*wind).normalized() if Vec2(*wind).length() > 1e-9 else Vec2(0.0, 0.0)
        self.spread_rate = float(spread_rate)
        self.burn_rate = float(burn_rate)
        self.fuel = [1.0] * (self.width * self.height)
        self.state = [UNBURNT] * (self.width * self.height)
        self._random = random.Random(seed)
        self.spread_events = 0

    def _index(self, x: int, y: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"cell ({x}, {y}) outside the fire grid")
        return y * self.width + x

    def ignite(self, x: int, y: int) -> bool:
        index = self._index(x, y)
        if self.state[index] != UNBURNT or self.fuel[index] <= 0:
            return False
        self.state[index] = BURNING
        return True

    def is_burning(self, x: int, y: int) -> bool:
        return self.state[self._index(x, y)] == BURNING

    def burning_cells(self) -> List[Tuple[int, int]]:
        return [
            (index % self.width, index // self.width)
            for index, value in enumerate(self.state)
            if value == BURNING
        ]

    def stats(self) -> FireStats:
        burning = self.state.count(BURNING)
        burnt = self.state.count(BURNT)
        return FireStats(burning, burnt, self.width * self.height - burning - burnt, self.spread_events)

    def step(self, dt: float) -> FireStats:
        if dt <= 0:
            raise ValueError("dt must be positive")
        ignitions: List[int] = []
        for y in range(self.height):
            for x in range(self.width):
                index = y * self.width + x
                if self.state[index] != BURNING:
                    continue
                self.fuel[index] -= self.burn_rate * dt
                if self.fuel[index] <= 0.0:
                    self.fuel[index] = 0.0
                    self.state[index] = BURNT
                    continue
                for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        continue
                    neighbour = ny * self.width + nx
                    if self.state[neighbour] != UNBURNT or self.fuel[neighbour] <= 0.05:
                        continue
                    if dx or dy:
                        direction = Vec2(dx, dy).normalized()
                        upwind = 1.0 + 1.4 * self.wind.dot(direction)
                        chance = self.spread_rate * (1.0 - self.moisture) * max(0.05, upwind) * dt
                    else:  # pragma: no cover - no zero offsets in the ring
                        chance = 0.0
                    if self._random.random() < chance:
                        ignitions.append(neighbour)
        for index in set(ignitions):
            if self.state[index] == UNBURNT:
                self.state[index] = BURNING
                self.spread_events += 1
        return self.stats()
