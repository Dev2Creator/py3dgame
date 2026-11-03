"""Provider contract and the small HTTP transport used by real adapters."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Iterator, Mapping, Tuple

from ..config import ProviderConfig, redact
from ..types import Capability, ChatRequest, ChatResponse, ErrorKind, ProviderError, StreamChunk

Transport = Callable[[str, str, Mapping[str, str], bytes | None, float], Tuple[int, Mapping[str, str], bytes]]


def urllib_transport(method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float):
    request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()
    except urllib.error.URLError as exc:
        raise ProviderError(ErrorKind.NETWORK, redact(str(exc.reason), *())[:200]) from exc
    except TimeoutError as exc:
        raise ProviderError(ErrorKind.TIMEOUT, "request timed out") from exc


class Provider:
    """Base adapter. Subclasses implement only what their API really supports."""

    name = "provider"

    def __init__(self, config: ProviderConfig, transport: Transport | None = None):
        self.config = config
        self._transport: Transport = transport or urllib_transport

    # -- capabilities -------------------------------------------------
    def capabilities(self) -> Capability:
        return Capability(chat=True)

    def list_models(self) -> list[str]:
        raise ProviderError(ErrorKind.UNSUPPORTED, "model listing is not supported", provider=self.name)

    def health(self) -> bool:
        try:
            self.list_models()
        except (ProviderError, NotImplementedError):
            return self.capabilities().chat
        return True

    # -- generation ---------------------------------------------------
    def chat(self, request: ChatRequest) -> ChatResponse:
        raise ProviderError(ErrorKind.UNSUPPORTED, "chat is not supported", provider=self.name)

    def stream(self, request: ChatRequest) -> Iterator[StreamChunk]:
        raise ProviderError(ErrorKind.UNSUPPORTED, "streaming is not supported", provider=self.name)

    # -- plumbing -----------------------------------------------------
    def _call(self, method: str, path: str, payload: dict | None, timeout: float) -> dict:
        self.config.validate_for_use()
        url = path if path.startswith("http") else f"{self.config.resolved_endpoint}{path}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        key = self.config.api_key()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        try:
            status, _headers, raw = self._transport(method, url, headers, body, timeout)
        except ProviderError as exc:
            raise ProviderError(exc.kind, redact(str(exc), key), provider=self.name) from None
        text = raw.decode("utf-8", "replace")
        if status >= 400:
            raise ProviderError(_status_kind(status), redact(f"HTTP {status}: {text[:300]}", key),
                                provider=self.name, status=status)
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError(ErrorKind.BAD_RESPONSE, f"malformed JSON: {exc.msg}",
                                provider=self.name, status=status) from None


def _status_kind(status: int) -> ErrorKind:
    if status in (401, 403):
        return ErrorKind.AUTH
    if status == 404:
        return ErrorKind.INVALID_REQUEST
    if status in (408, 504):
        return ErrorKind.TIMEOUT
    if status == 429:
        return ErrorKind.RATE_LIMIT
    if status >= 500:
        return ErrorKind.SERVER
    return ErrorKind.INVALID_REQUEST
