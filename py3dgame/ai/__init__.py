"""Optional, provider-neutral AI subsystem.

Nothing here is imported by the renderer, physics or scene code: the engine runs
without it and without network access.
"""

from .config import ProviderConfig, redact
from .jobs import AIJobSystem
from .providers import MockProvider, OllamaProvider, OpenAICompatibleProvider, Provider, Transport, urllib_transport
from .runtime import AIResult, AIRuntime, AIStats, CancelToken, build_provider
from .types import (
    AIError,
    Capability,
    ChatRequest,
    ChatResponse,
    ErrorKind,
    GenerationParams,
    Message,
    ProviderError,
    Role,
    StreamChunk,
    Usage,
)

__all__ = [
    "AIError",
    "AIJobSystem",
    "AIResult",
    "AIRuntime",
    "AIStats",
    "CancelToken",
    "Capability",
    "ChatRequest",
    "ChatResponse",
    "ErrorKind",
    "GenerationParams",
    "Message",
    "MockProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "Provider",
    "ProviderConfig",
    "ProviderError",
    "Role",
    "StreamChunk",
    "Transport",
    "Usage",
    "build_provider",
    "redact",
    "urllib_transport",
]
