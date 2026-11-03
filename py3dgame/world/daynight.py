"""Time-of-day lighting, the way Dunia drives its world clock.

The model is intentionally small and testable: a 24-hour clock, an elevation
curve, and a colour palette that is interpolated between key moments. It feeds
lights and fog; it does not render anything by itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from ..math3d import Vec3

Colour = Tuple[int, int, int]

# hour, sun colour, ambient colour, sky colour, sun intensity, ambient intensity
KEYS: List[Tuple[float, Colour, Colour, Colour, float, float]] = [
    (0.0, (8, 10, 26), (8, 10, 20), (4, 6, 18), 0.0, 0.08),
    (4.5, (8, 10, 26), (10, 12, 24), (6, 8, 22), 0.0, 0.09),
    (6.5, (255, 138, 92), (72, 66, 82), (70, 90, 140), 0.55, 0.22),
    (9.0, (255, 246, 232), (128, 140, 160), (120, 170, 226), 1.0, 0.35),
    (15.0, (255, 250, 240), (130, 142, 160), (110, 165, 226), 1.0, 0.35),
    (18.0, (255, 120, 70), (82, 66, 80), (92, 88, 130), 0.6, 0.24),
    (20.0, (20, 22, 40), (14, 16, 30), (10, 12, 32), 0.05, 0.1),
    (24.0, (8, 10, 26), (8, 10, 20), (4, 6, 18), 0.0, 0.08),
]


def _mix(first: Colour, second: Colour, t: float) -> Colour:
    return tuple(int(round(first[i] + (second[i] - first[i]) * t)) for i in range(3))


@dataclass(frozen=True)
class SunState:
    hour: float
    elevation: float          # degrees above the horizon
    azimuth: float            # degrees around the horizon
    sun_colour: Colour
    ambient_colour: Colour
    sky_colour: Colour
    sun_intensity: float
    ambient_intensity: float


class DayNightCycle:
    def __init__(
        self,
        start_hour: float = 6.0,
        day_length_hours: float = 24.0,
        latitude: float = 22.5,
    ):
        if not 0.0 <= start_hour < 24.0:
            raise ValueError("start_hour must be within 0..24")
        if day_length_hours <= 0:
            raise ValueError("day_length_hours must be positive")
        if not -66.0 <= latitude <= 66.0:
            raise ValueError("latitude must be within -66..66")
        self.hour = float(start_hour)
        self.day_length_hours = float(day_length_hours)
        self.latitude = float(latitude)
        self.day = 0

    def set_hour(self, hour: float) -> float:
        self.hour = float(hour) % 24.0
        return self.hour

    def advance(self, seconds: float) -> float:
        """Advance by real seconds, honouring a shortened or lengthened day."""
        if seconds < 0:
            raise ValueError("cannot advance negative time")
        hours = (seconds / 3600.0) * (24.0 / self.day_length_hours)
        self.hour += hours
        while self.hour >= 24.0:
            self.hour -= 24.0
            self.day += 1
        return self.hour

    def _max_elevation(self) -> float:
        return max(5.0, 90.0 - abs(self.latitude - 23.44))

    def elevation(self) -> float:
        angle = (self.hour - 6.0) / 12.0 * math.pi
        return math.sin(angle) * self._max_elevation()

    def azimuth(self) -> float:
        return (self.hour / 24.0) * 360.0

    def sun_direction(self) -> Vec3:
        elevation = math.radians(self.elevation())
        azimuth = math.radians(self.azimuth())
        return Vec3(
            math.cos(elevation) * math.cos(azimuth),
            math.sin(elevation),
            math.cos(elevation) * math.sin(azimuth),
        )

    def state(self) -> SunState:
        for index in range(len(KEYS) - 1):
            start_hour, *start_values = KEYS[index]
            end_hour, *end_values = KEYS[index + 1]
            if start_hour <= self.hour <= end_hour:
                span = end_hour - start_hour
                t = 0.0 if span == 0 else (self.hour - start_hour) / span
                sun = _mix(start_values[0], end_values[0], t)
                ambient = _mix(start_values[1], end_values[1], t)
                sky = _mix(start_values[2], end_values[2], t)
                sun_intensity = start_values[3] + (end_values[3] - start_values[3]) * t
                ambient_intensity = start_values[4] + (end_values[4] - start_values[4]) * t
                break
        else:  # pragma: no cover - KEYS always covers 0..24
            raise RuntimeError("day/night palette does not cover this hour")
        return SunState(
            hour=self.hour,
            elevation=self.elevation(),
            azimuth=self.azimuth(),
            sun_colour=sun,
            ambient_colour=ambient,
            sky_colour=sky,
            sun_intensity=max(0.0, sun_intensity * max(0.0, math.sin(math.radians(self.elevation() + 4.0)))),
            ambient_intensity=max(0.0, ambient_intensity),
        )
