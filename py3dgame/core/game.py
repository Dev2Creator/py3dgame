"""Application lifecycle: window, fixed-timestep loop, input and drawing.

The loop separates simulation from presentation. ``advance(dt)`` runs zero or
more fixed logic steps and exposes ``alpha`` for interpolation; ``draw()``
presents one frame. ``run()`` wires both to a real clock, and tests drive
``advance``/``draw`` directly so nothing depends on wall-clock timing.
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional

from ..exceptions import ConfigurationError
from ..input.manager import InputState
from ..platform.events import Quit, Resize
from ..platform.window import Window, create_window
from ..renderer2d.canvas import Canvas
from .scene import Scene

__all__ = ["Game"]

Hook = Callable[[float], None]
DrawHook = Callable[[Canvas], None]


class Game:
    """Owns the window, the canvas, input state and the loop."""

    def __init__(
        self,
        title: str = "py3dgame",
        width: int = 1280,
        height: int = 720,
        fps: int = 60,
        fixed_dt: float = 1.0 / 60.0,
        window: str = "auto",
        max_substeps: int = 5,
    ) -> None:
        if fps <= 0:
            raise ConfigurationError("fps must be positive")
        if not 0.0 < fixed_dt <= 1.0:
            raise ConfigurationError("fixed_dt must be in (0, 1] seconds")
        if max_substeps < 1:
            raise ConfigurationError("max_substeps must be at least 1")

        self.title = title
        self.fps = float(fps)
        self.fixed_dt = float(fixed_dt)
        self.max_substeps = int(max_substeps)

        self.window: Window = create_window(title, width, height, backend=window)
        self.canvas = Canvas(width, height)
        self.input = InputState()

        self.scene: Optional[Scene] = None
        self.frame_count = 0
        self.simulated_time = 0.0
        self.alpha = 0.0
        self.dropped_steps = 0

        self._running = False
        self._accumulator = 0.0
        self._update_hooks: List[Hook] = []
        self._draw_hooks: List[DrawHook] = []
        self._clock = time.perf_counter

    # -- configuration ------------------------------------------------ #
    @property
    def running(self) -> bool:
        return self._running

    @property
    def background(self):
        return self.scene.background if self.scene is not None else (12, 12, 16, 255)

    def load_scene(self, scene: Scene) -> Scene:
        if not isinstance(scene, Scene):
            raise ConfigurationError("load_scene expects a Scene instance")
        self.scene = scene
        return scene

    def on_update(self, hook: Hook) -> Hook:
        self._update_hooks.append(hook)
        return hook

    def on_draw(self, hook: DrawHook) -> DrawHook:
        self._draw_hooks.append(hook)
        return hook

    def stop(self) -> None:
        self._running = False

    def close(self) -> None:
        self._running = False
        self.window.close()

    # -- simulation --------------------------------------------------- #
    def step(self, dt: Optional[float] = None) -> None:
        """Run exactly one logic tick."""
        delta = self.fixed_dt if dt is None else float(dt)
        if delta < 0:
            raise ValueError("dt must not be negative")
        self.simulated_time += delta
        if self.scene is not None:
            self.scene.update(delta)
        for hook in self._update_hooks:
            hook(delta)

    def advance(self, real_dt: float) -> int:
        """Accumulate real time and run as many fixed steps as it earned."""
        real_dt = float(real_dt)
        if real_dt < 0:
            raise ValueError("real_dt must not be negative")
        self._accumulator += real_dt
        steps = 0
        while self._accumulator >= self.fixed_dt and steps < self.max_substeps:
            self.step(self.fixed_dt)
            self._accumulator -= self.fixed_dt
            steps += 1
        if self._accumulator >= self.fixed_dt:
            # We are behind by more than max_substeps: drop the backlog instead of
            # spiralling, but keep the fractional phase so motion stays smooth.
            self.dropped_steps += 1
            self._accumulator %= self.fixed_dt
        self.alpha = self._accumulator / self.fixed_dt if self.fixed_dt else 0.0
        return steps

    # -- presentation -------------------------------------------------- #
    def draw(self) -> None:
        self.canvas.clear(self.background)
        # Scene rendering arrives with the sprite renderer; draw hooks own
        # presentation until then.
        for hook in self._draw_hooks:
            hook(self.canvas)
        self.window.present(self.canvas)
        self.frame_count += 1

    def pump(self) -> None:
        for event in self.window.poll_events():
            if isinstance(event, Quit):
                self.stop()
                continue
            if isinstance(event, Resize):
                self.canvas.resize(event.width, event.height)
            self.input.handle_event(event)

    # -- main loop ------------------------------------------------------ #
    def run(self, max_frames: Optional[int] = None) -> int:
        """Blocking loop. ``max_frames`` bounds it, which tests rely on."""
        self._running = True
        last = self._clock()
        target = 1.0 / self.fps
        try:
            while self._running:
                self.pump()
                now = self._clock()
                real_dt = max(0.0, now - last)
                last = now
                self.advance(real_dt)
                self.draw()
                self.input.end_frame()
                if max_frames is not None and self.frame_count >= max_frames:
                    break
                if real_dt < target:
                    time.sleep(target - real_dt)
        finally:
            self._running = False
            self.window.close()
        return self.frame_count

    def __repr__(self) -> str:
        return (
            f"Game(title={self.title!r}, {self.canvas.width}x{self.canvas.height}, "
            f"fps={self.fps:g}, frames={self.frame_count})"
        )
