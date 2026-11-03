"""AI dialogue that stays off the game loop.

Runs offline with the mock provider. Point it at a local Ollama server with:

    P3D_AI_PROVIDER=ollama P3D_AI_MODEL=llama3 python examples/ai_dialogue.py
"""

from __future__ import annotations

import os

import py3dgame as p3d

PROMPT = "You are the ferry keeper. The 18:10 crossing is delayed. Reply in one short line."


def build_runtime() -> p3d.AIRuntime:
    provider = os.environ.get("P3D_AI_PROVIDER", "mock")
    if provider == "ollama":
        config = p3d.ProviderConfig(provider="ollama", model=os.environ.get("P3D_AI_MODEL", "llama3"))
        return p3d.AIRuntime(config, p3d.OllamaProvider(config))
    config = p3d.ProviderConfig(provider="mock", model="mock-small")
    return p3d.AIRuntime(config, p3d.MockProvider(reply="Ferry's late again. Sit tight, the kettle's on."))


def main() -> None:
    game = p3d.Game(title="py3dgame · AI dialogue", width=320, height=180, fps=60)
    runtime = build_runtime()
    jobs = p3d.AIJobSystem(runtime)
    lines: list[str] = []
    submitted = False

    @game.on_update
    def update(dt: float) -> None:
        nonlocal submitted
        if not submitted:
            jobs.submit([p3d.Message("user", PROMPT)])
            submitted = True
        for result in jobs.update():
            if result.ok:
                lines.append(result.response.text)
                print(f"npc ({result.provider}): {result.response.text}")

    limit = 90 if isinstance(game.window, p3d.HeadlessWindow) else None
    game.run(max_frames=limit)
    jobs.shutdown()
    print(f"frames={game.frame_count} replies={len(lines)} provider={runtime.provider.name}")


if __name__ == "__main__":
    main()
