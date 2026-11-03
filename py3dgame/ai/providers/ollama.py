"""Ollama adapter (local HTTP server, default http://127.0.0.1:11434)."""

from __future__ import annotations

from ..types import Capability, ChatRequest, ChatResponse, ErrorKind, ProviderError, Usage
from .base import Provider


class OllamaProvider(Provider):
    name = "ollama"

    def capabilities(self) -> Capability:
        # Honest list: no streaming, embeddings or tool calling implemented yet.
        return Capability(chat=True, json_mode=True, model_listing=True, usage_reporting=True)

    def chat(self, request: ChatRequest) -> ChatResponse:
        payload = {
            "model": request.model,
            "messages": [m.to_dict() for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.params.temperature,
                "top_p": request.params.top_p,
                "num_predict": request.params.max_tokens,
            },
        }
        data = self._call("POST", "/api/chat", payload, request.timeout)
        message = data.get("message")
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str):
            raise ProviderError(ErrorKind.BAD_RESPONSE, "response has no message.content", provider=self.name)
        usage = Usage(prompt_tokens=int(data.get("prompt_eval_count") or 0),
                      completion_tokens=int(data.get("eval_count") or 0))
        return ChatResponse(text=text, model=str(data.get("model") or request.model),
                            provider=self.name, usage=usage,
                            finish_reason=str(data.get("done_reason") or "stop"))

    def list_models(self) -> list[str]:
        data = self._call("GET", "/api/tags", None, min(self.config.timeout, 10.0))
        models = data.get("models")
        if not isinstance(models, list):
            raise ProviderError(ErrorKind.BAD_RESPONSE, "response has no models list", provider=self.name)
        names = [str(entry.get("name")) for entry in models if isinstance(entry, dict) and entry.get("name")]
        if not names:
            raise ProviderError(ErrorKind.BAD_RESPONSE, "provider reports no installed models", provider=self.name)
        return names
