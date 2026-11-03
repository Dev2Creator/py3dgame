"""OpenAI-compatible adapter: OpenAI itself, LM Studio, vLLM, llama.cpp server."""

from __future__ import annotations

from ..types import Capability, ChatRequest, ChatResponse, ErrorKind, ProviderError, Usage
from .base import Provider


class OpenAICompatibleProvider(Provider):
    name = "openai"

    def capabilities(self) -> Capability:
        return Capability(chat=True, json_mode=True, tool_calling=True, model_listing=True, usage_reporting=True)

    def chat(self, request: ChatRequest) -> ChatResponse:
        payload = {
            "model": request.model,
            "messages": [m.to_dict() for m in request.messages],
            "temperature": request.params.temperature,
            "top_p": request.params.top_p,
            "max_tokens": request.params.max_tokens,
        }
        if request.params.stop:
            payload["stop"] = list(request.params.stop)
        data = self._call("POST", "/chat/completions", payload, request.timeout)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError(ErrorKind.BAD_RESPONSE, "response has no choices", provider=self.name)
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        text = message.get("content")
        if not isinstance(text, str):
            raise ProviderError(ErrorKind.BAD_RESPONSE, "response has no message content", provider=self.name)
        usage_data = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        usage = Usage(prompt_tokens=int(usage_data.get("prompt_tokens") or 0),
                      completion_tokens=int(usage_data.get("completion_tokens") or 0))
        return ChatResponse(text=text, model=str(data.get("model") or request.model), provider=self.name,
                            usage=usage, finish_reason=str(first.get("finish_reason") or "stop"))

    def list_models(self) -> list[str]:
        data = self._call("GET", "/models", None, min(self.config.timeout, 10.0))
        entries = data.get("data")
        if not isinstance(entries, list):
            raise ProviderError(ErrorKind.BAD_RESPONSE, "response has no data list", provider=self.name)
        return [str(entry.get("id")) for entry in entries if isinstance(entry, dict) and entry.get("id")]
