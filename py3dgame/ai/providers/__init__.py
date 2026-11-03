"""Provider adapters. Every one exposes capability metadata it can actually honour."""

from .base import Provider, Transport, urllib_transport
from .mock import MockProvider
from .ollama import OllamaProvider
from .openai_compat import OpenAICompatibleProvider

__all__ = [
    "MockProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "Provider",
    "Transport",
    "urllib_transport",
]
