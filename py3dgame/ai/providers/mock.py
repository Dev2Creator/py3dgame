"""Deterministic in-process provider used by tests, demos and offline mode."""

from __future__ import annotations

from typing import Callable, Iterator

from ..config import ProviderConfig
from ..types import Capability, ChatRequest, ChatResponse, ErrorKind, GenerationParams, ProviderError, StreamChunk, Usage
from .base import Provider


class MockProvider(Provider):
    name = "mock"

    def __init__(self, config: ProviderConfig | None = None, reply: str = "The kettle is on.",
                 responder: Callable[[ChatRequest], str] | None = None, failures: int = 0, failure_kind: ErrorKind = ErrorKind.SERVER):
        super().__init__(config or ProviderConfig(provider="mock", model="mock-small"))
        self.reply = reply
        self.responder = responder
        self._failures = int(failures)
        self._failure_kind = failure_kind
        self.requests: list[ChatRequest] = []

    def capabilities(self) -> Capability:
        return Capability(chat=True, streaming=True, json_mode=True, usage_reporting=True, model_listing=True)

    def list_models(self) -> list[str]:
        return ["mock-small", "mock-large"]

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        if self._failures > 0:
            self._failures -= 1
            raise ProviderError(self._failure_kind, "injected failure", provider=self.name)
        text = self.responder(request) if self.responder else self.reply
        return ChatResponse(text=text, model=request.model, provider=self.name,
                            usage=Usage(prompt_tokens=len(request.messages), completion_tokens=len(text.split())))

    def stream(self, request: ChatRequest) -> Iterator[StreamChunk]:
        text = self.chat(request).text
        for word in text.split():
            yield StreamChunk(text=word + " ")
        yield StreamChunk(text="", done=True)
