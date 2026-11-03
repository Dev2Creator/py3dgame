"""Provider-neutral types for the optional AI subsystem.

Adapters translate provider responses into these models so game code never
depends on a specific vendor payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence, Tuple

from ..exceptions import Py3DGameError


class AIError(Py3DGameError):
    """Base class for AI subsystem failures."""


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ErrorKind(str, Enum):
    AUTH = "auth"
    NETWORK = "network"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    CANCELLED = "cancelled"
    BAD_RESPONSE = "bad_response"
    UNSUPPORTED = "unsupported"


_RETRYABLE = {ErrorKind.NETWORK, ErrorKind.TIMEOUT, ErrorKind.RATE_LIMIT, ErrorKind.SERVER}


class ProviderError(AIError):
    """A provider call failed. Never carries credentials in its message."""

    def __init__(self, kind: ErrorKind | str, message: str, *, provider: str = "", status: int | None = None):
        self.kind = ErrorKind(kind)
        self.provider = provider
        self.status = status
        super().__init__(f"{provider + ': ' if provider else ''}{message}")

    @property
    def retryable(self) -> bool:
        return self.kind in _RETRYABLE


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    name: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.role, Role):
            object.__setattr__(self, "role", Role(self.role))
        if not self.content or not self.content.strip():
            raise ValueError("message content must not be empty")

    def to_dict(self) -> dict:
        payload = {"role": self.role.value, "content": self.content}
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class GenerationParams:
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 1.0
    stop: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.temperature) <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        if int(self.max_tokens) <= 0:
            raise ValueError("max_tokens must be positive")
        if not 0.0 < float(self.top_p) <= 1.0:
            raise ValueError("top_p must be in (0, 1]")


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: Tuple[Message, ...]
    params: GenerationParams = field(default_factory=GenerationParams)
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("model must not be empty")
        if not self.messages:
            raise ValueError("at least one message is required")
        if float(self.timeout) <= 0:
            raise ValueError("timeout must be positive")

    @classmethod
    def build(cls, model: str, messages: Sequence[Message], **kwargs) -> "ChatRequest":
        return cls(model=model, messages=tuple(messages), **kwargs)


@dataclass(frozen=True)
class ChatResponse:
    text: str
    model: str
    provider: str
    usage: Usage = field(default_factory=Usage)
    finish_reason: str = "stop"


@dataclass(frozen=True)
class StreamChunk:
    text: str
    done: bool = False


@dataclass(frozen=True)
class Capability:
    """What an adapter actually supports. Never assume parity between providers."""

    chat: bool = False
    streaming: bool = False
    json_mode: bool = False
    tool_calling: bool = False
    embeddings: bool = False
    image_input: bool = False
    model_listing: bool = False
    usage_reporting: bool = False

    def as_dict(self) -> Mapping[str, bool]:
        return {
            "chat": self.chat,
            "streaming": self.streaming,
            "json_mode": self.json_mode,
            "tool_calling": self.tool_calling,
            "embeddings": self.embeddings,
            "image_input": self.image_input,
            "model_listing": self.model_listing,
            "usage_reporting": self.usage_reporting,
        }
