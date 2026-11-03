"""Bounded, cancellable AI execution that never blocks the game loop."""

from __future__ import annotations

import random
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Deque, Dict, List, Optional, Sequence

from .config import ProviderConfig
from .providers.base import Provider, Transport
from .providers.mock import MockProvider
from .providers.ollama import OllamaProvider
from .providers.openai_compat import OpenAICompatibleProvider
from .types import (
    AIError,
    ChatRequest,
    ChatResponse,
    ErrorKind,
    GenerationParams,
    Message,
    ProviderError,
)

_PROVIDERS = {"mock": MockProvider, "ollama": OllamaProvider, "openai": OpenAICompatibleProvider}


def build_provider(config: ProviderConfig, transport: Transport | None = None) -> Provider:
    cls = _PROVIDERS[config.provider]
    return cls(config, transport) if transport is not None else cls(config=config)


@dataclass
class AIStats:
    submitted: int = 0
    completed: int = 0
    failed: int = 0
    retried: int = 0
    cancelled: int = 0
    cache_hits: int = 0

    def snapshot(self) -> Dict[str, int]:
        return {name: getattr(self, name) for name in
                ("submitted", "completed", "failed", "retried", "cancelled", "cache_hits")}


@dataclass(frozen=True)
class AIResult:
    job_id: str
    provider: str
    ok: bool
    response: Optional[ChatResponse] = None
    error: Optional[ProviderError] = None
    data: Optional[dict] = None
    duration: float = 0.0
    cached: bool = False


class CancelToken:
    __slots__ = ("_cancelled",)

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise ProviderError(ErrorKind.CANCELLED, "job cancelled")


@dataclass
class _Job:
    id: str
    request: ChatRequest
    token: CancelToken
    key: Optional[str]


class AIRuntime:
    """Submits AI work to a small pool and hands results back through poll()."""

    def __init__(self, config: ProviderConfig | None = None, provider: Provider | None = None, *,
                 transport: Transport | None = None, sleep: Callable[[float], None] = time.sleep):
        self.config = config or ProviderConfig(provider="mock", model="mock-small")
        self.provider = provider or build_provider(self.config, transport)
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrency,
                                            thread_name_prefix="p3d-ai")
        self._lock = threading.Lock()
        self._pending: Dict[str, _Job] = {}
        self._results: Deque[AIResult] = deque()
        self._cache: Dict[str, ChatResponse] = {}
        self._sleep = sleep
        self._closed = False
        self.stats = AIStats()

    # -- public -------------------------------------------------------
    def submit(self, messages: Sequence[Message], *, model: str | None = None,
               params: GenerationParams | None = None, timeout: float | None = None) -> str:
        if self._closed:
            raise AIError("AI runtime has been shut down")
        request = ChatRequest.build(model or self.config.model, messages,
                                    params=params or GenerationParams(),
                                    timeout=timeout or self.config.timeout)
        with self._lock:
            if len(self._pending) >= self.config.queue_limit:
                raise AIError(f"AI queue is full ({self.config.queue_limit}); poll results before submitting more")
        job_id = uuid.uuid4().hex[:12]
        key = self._cache_key(request) if self.config.cache else None
        if key is not None:
            with self._lock:
                cached = self._cache.get(key)
            if cached is not None:
                with self._lock:
                    self.stats.submitted += 1
                    self.stats.completed += 1
                    self.stats.cache_hits += 1
                    self._results.append(AIResult(job_id, self.provider.name, True, response=cached, cached=True))
                return job_id
        job = _Job(job_id, request, CancelToken(), key)
        with self._lock:
            self._pending[job_id] = job
            self.stats.submitted += 1
        self._executor.submit(self._run, job)
        return job_id

    def poll(self, max_results: int = 8) -> List[AIResult]:
        out: List[AIResult] = []
        with self._lock:
            while self._results and len(out) < max(1, int(max_results)):
                out.append(self._results.popleft())
        return out

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._pending.get(job_id)
            if job is None:
                return False
            job.token.cancel()
            self.stats.cancelled += 1
        return True

    def in_flight(self) -> int:
        with self._lock:
            return len(self._pending)

    def health(self) -> bool:
        return self.provider.health()

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            self._closed = True
            jobs = list(self._pending.values())
        for job in jobs:
            job.token.cancel()
        self._executor.shutdown(wait=wait)

    # -- internals ----------------------------------------------------
    def _run(self, job: _Job) -> None:
        started = time.perf_counter()
        result: AIResult
        try:
            response = self._with_retries(job)
            if job.key is not None:
                with self._lock:
                    self._cache[job.key] = response
            result = AIResult(job.id, self.provider.name, True, response=response,
                              duration=time.perf_counter() - started)
        except ProviderError as exc:
            result = AIResult(job.id, self.provider.name, False, error=exc,
                              duration=time.perf_counter() - started)
        except Exception as exc:  # boundary: never let a worker die silently
            result = AIResult(job.id, self.provider.name, False,
                              error=ProviderError(ErrorKind.BAD_RESPONSE, f"provider raised {type(exc).__name__}",
                                                 provider=self.provider.name),
                              duration=time.perf_counter() - started)
        with self._lock:
            self._pending.pop(job.id, None)
            self._results.append(result)
            if result.ok:
                self.stats.completed += 1
            else:
                self.stats.failed += 1

    def _with_retries(self, job: _Job) -> ChatResponse:
        attempt = 0
        while True:
            job.token.raise_if_cancelled()
            try:
                response = self.provider.chat(job.request)
                # A blocking HTTP call cannot be interrupted, so a cancellation
                # that arrived in flight discards the result instead.
                job.token.raise_if_cancelled()
                return response
            except ProviderError as exc:
                if not exc.retryable or attempt >= self.config.max_retries:
                    raise
                attempt += 1
                with self._lock:
                    self.stats.retried += 1
                delay = min(1.0, 0.05 * (2 ** (attempt - 1))) * (1.0 + random.random() * 0.2)
                self._sleep(delay)

    @staticmethod
    def _cache_key(request: ChatRequest) -> str:
        parts = [request.model, f"{request.params.temperature}", f"{request.params.max_tokens}",
                 f"{request.params.top_p}"]
        parts.extend(f"{m.role.value}:{m.content}" for m in request.messages)
        return "|".join(parts)
