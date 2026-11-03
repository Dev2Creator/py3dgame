"""Provider configuration with explicit, validated settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from .types import AIError

_DEFAULT_ENDPOINTS = {
    "ollama": "http://127.0.0.1:11434",
    "openai": "https://api.openai.com/v1",
    "mock": "mock://local",
}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def redact(text: str, *secrets: str | None) -> str:
    """Remove secrets from a message before it can reach logs or exceptions."""
    cleaned = text
    for secret in secrets:
        if secret and len(secret) >= 4:
            cleaned = cleaned.replace(secret, "[redacted]")
    return cleaned


@dataclass
class ProviderConfig:
    provider: str = "ollama"
    model: str = "llama3"
    endpoint: str | None = None
    api_key_env: str | None = None
    timeout: float = 30.0
    max_retries: int = 2
    max_concurrency: int = 2
    queue_limit: int = 32
    allow_remote: bool = False
    cache: bool = False

    def __post_init__(self) -> None:
        if self.provider not in _DEFAULT_ENDPOINTS:
            raise AIError(f"unknown provider {self.provider!r}; known: {', '.join(sorted(_DEFAULT_ENDPOINTS))}")
        if not self.model:
            raise AIError("model must not be empty")
        if float(self.timeout) <= 0:
            raise AIError("timeout must be positive")
        if int(self.max_retries) < 0:
            raise AIError("max_retries must be >= 0")
        if int(self.max_concurrency) < 1:
            raise AIError("max_concurrency must be >= 1")
        if int(self.queue_limit) < 1:
            raise AIError("queue_limit must be >= 1")

    @property
    def resolved_endpoint(self) -> str:
        return (self.endpoint or _DEFAULT_ENDPOINTS[self.provider]).rstrip("/")

    @property
    def host(self) -> str:
        endpoint = self.resolved_endpoint
        if "://" not in endpoint:
            return endpoint
        return endpoint.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]

    @property
    def is_remote(self) -> bool:
        return self.host not in _LOCAL_HOSTS

    def api_key(self, environ: Mapping[str, str] | None = None) -> str | None:
        env = os.environ if environ is None else environ
        if not self.api_key_env:
            return None
        value = env.get(self.api_key_env)
        return value or None

    def validate_for_use(self, environ: Mapping[str, str] | None = None) -> None:
        """Fail loudly before a request, not in the middle of one."""
        if self.is_remote and not self.allow_remote:
            raise AIError(
                f"refusing remote provider {self.provider!r} at {self.host!r}: "
                "set allow_remote=True after reviewing what data will be sent"
            )
        if self.provider == "openai" and self.is_remote and not self.api_key(environ):
            raise AIError(f"provider {self.provider!r} needs an API key in env {self.api_key_env or '(unset api_key_env)'}")

    def describe(self) -> str:
        return f"{self.provider}:{self.model} @ {self.resolved_endpoint}"
