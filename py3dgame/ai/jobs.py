"""Game-loop-safe facade: submit work, call update() from the fixed step."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Callable, Dict, List, Optional, Sequence

from .runtime import AIResult, AIRuntime
from .types import ErrorKind, GenerationParams, Message, ProviderError

Validator = Callable[[object], dict]


class AIJobSystem:
    def __init__(self, runtime: AIRuntime, validator: Validator | None = None):
        self.runtime = runtime
        self.validator = validator
        self._callbacks: Dict[str, Callable[[AIRESult], None]] = {}

    def submit(self, messages: Sequence[Message], callback: Callable[["AIRESult"], None] | None = None,
               **kwargs) -> str:
        job_id = self.runtime.submit(messages, **kwargs)
        if callback is not None:
            self._callbacks[job_id] = callback
        return job_id

    def update(self, max_results: int = 8) -> List["AIRESult"]:
        results: List["AIRESult"] = []
        for result in self.runtime.poll(max_results):
            validated = self._validate(result)
            callback = self._callbacks.pop(validated.job_id, None)
            if callback is not None:
                callback(validated)
            results.append(validated)
        return results

    def shutdown(self, wait: bool = True) -> None:
        self.runtime.shutdown(wait=wait)

    def _validate(self, result: AIRESult) -> AIRESult:
        if not result.ok or self.validator is None or result.response is None:
            return result
        try:
            payload = json.loads(result.response.text)
        except (json.JSONDecodeError, TypeError):
            return replace(result, ok=False, data=None,
                           error=ProviderError(ErrorKind.BAD_RESPONSE, "AI output was not valid JSON",
                                               provider=result.provider))
        try:
            data = self.validator(payload)
        except Exception as exc:  # boundary: validator rejects untrusted model output
            return replace(result, ok=False, data=None,
                           error=ProviderError(ErrorKind.INVALID_REQUEST,
                                               f"AI output rejected by validator: {exc}", provider=result.provider))
        return replace(result, data=data if isinstance(data, dict) else {"value": data})
