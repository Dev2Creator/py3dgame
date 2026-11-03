"""AI subsystem: contracts, adapters, retries, cancellation, game-loop safety."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import py3dgame as p3d
from py3dgame.ai import (
    AIError,
    AIJobSystem,
    AIRuntime,
    ChatRequest,
    ErrorKind,
    GenerationParams,
    Message,
    MockProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderError,
    redact,
)

FAST = ProviderConfig(provider="mock", model="mock-small", max_retries=2, max_concurrency=2, queue_limit=8)


def wait_results(runtime: AIRuntime, count: int = 1, timeout: float = 5.0):
    deadline = time.time() + timeout
    out = []
    while len(out) < count and time.time() < deadline:
        out.extend(runtime.poll(8))
        if len(out) < count:
            time.sleep(0.01)
    return out


class Stub:
    """A real localhost HTTP server so adapters exercise the actual urllib path."""

    def __init__(self, routes):
        self.routes = routes
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                outer._handle(self, "GET")

            def do_POST(self):
                outer._handle(self, "POST")

            def log_message(self, *args):
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _handle(self, handler, method):
        length = int(handler.headers.get("Content-Length") or 0)
        raw_body = handler.rfile.read(length) if length else b""
        path = handler.path.split("?")[0]
        self.requests.append((method, path, raw_body, dict(handler.headers)))
        route = self.routes.get((method, path))
        if route is None:
            status, payload = 404, {"error": "not found"}
        elif callable(route):
            status, payload = route(json.loads(raw_body) if raw_body else {})
        else:
            status, payload = route
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def test_message_and_request_validation():
    with pytest.raises(ValueError):
        Message(role=p3d.Role.USER, content="   ")
    request = ChatRequest.build("m", [Message("user", "hello")])
    assert request.messages[0].role is p3d.Role.USER
    with pytest.raises(ValueError):
        ChatRequest(model="", messages=(Message("user", "x"),))
    with pytest.raises(ValueError):
        GenerationParams(temperature=3.0)
    with pytest.raises(ValueError):
        GenerationParams(max_tokens=0)


def test_config_guards_remote_providers():
    local = ProviderConfig(provider="ollama")
    assert not local.is_remote
    remote = ProviderConfig(provider="ollama", endpoint="https://example.com")
    assert remote.is_remote
    with pytest.raises(AIError):
        remote.validate_for_use()
    remote.allow_remote = True
    remote.validate_for_use()
    openai = ProviderConfig(provider="openai", allow_remote=True, api_key_env="P3D_TEST_KEY")
    with pytest.raises(AIError):
        openai.validate_for_use(environ={})
    openai.validate_for_use(environ={"P3D_TEST_KEY": "sk-secret-value"})
    with pytest.raises(AIError):
        ProviderConfig(provider="not-a-provider")


def test_redaction_removes_secrets():
    assert "sk-123456" not in redact("auth failed for sk-123456", "sk-123456")
    assert redact("short", "ab") == "short"


def test_mock_provider_is_deterministic_and_reports_usage():
    provider = MockProvider()
    response = provider.chat(ChatRequest.build("mock-small", [Message("user", "hi")]))
    assert response.text == "The kettle is on."
    assert response.usage.total_tokens > 0
    assert provider.capabilities().chat and provider.capabilities().model_listing


def test_runtime_returns_results_without_blocking():
    runtime = AIRuntime(FAST, MockProvider())
    started = time.perf_counter()
    job_id = runtime.submit([Message("user", "hello")])
    submit_ms = (time.perf_counter() - started) * 1000
    assert submit_ms < 50, f"submit blocked the caller for {submit_ms:.1f}ms"
    results = wait_results(runtime)
    runtime.shutdown()
    assert results[0].job_id == job_id
    assert results[0].ok and results[0].response.text


def test_queue_limit_is_enforced():
    slow = MockProvider(responder=lambda req: (time.sleep(0.2) or "slow"))
    runtime = AIRuntime(ProviderConfig(provider="mock", model="m", queue_limit=1), slow)
    runtime.submit([Message("user", "one")])
    with pytest.raises(AIError):
        runtime.submit([Message("user", "two")])
    wait_results(runtime, timeout=3)
    runtime.shutdown()


def test_retries_transient_errors_only():
    flaky = MockProvider(failures=2)
    runtime = AIRuntime(FAST, flaky)
    runtime.submit([Message("user", "hi")])
    results = wait_results(runtime)
    runtime.shutdown()
    assert results[0].ok
    assert runtime.stats.retried == 2

    fatal = MockProvider(failures=1, failure_kind=ErrorKind.INVALID_REQUEST)
    runtime = AIRuntime(FAST, fatal)
    runtime.submit([Message("user", "hi")])
    results = wait_results(runtime)
    runtime.shutdown()
    assert not results[0].ok
    assert results[0].error.kind is ErrorKind.INVALID_REQUEST
    assert runtime.stats.retried == 0


def test_cancellation_produces_cancelled_result():
    slow = MockProvider(responder=lambda req: (time.sleep(0.25) or "late"))
    runtime = AIRuntime(FAST, slow)
    job_id = runtime.submit([Message("user", "cancel me")])
    assert runtime.cancel(job_id)
    results = wait_results(runtime, timeout=5)
    runtime.shutdown()
    assert results and not results[0].ok
    assert results[0].error.kind is ErrorKind.CANCELLED


def test_cache_is_opt_in():
    provider = MockProvider()
    config = ProviderConfig(provider="mock", model="m", cache=True)
    runtime = AIRuntime(config, provider)
    runtime.submit([Message("user", "same")])
    wait_results(runtime)
    runtime.submit([Message("user", "same")])
    results = wait_results(runtime)
    runtime.shutdown()
    assert results[0].cached
    assert runtime.stats.cache_hits == 1

    provider2 = MockProvider()
    runtime2 = AIRuntime(FAST, provider2)
    runtime2.submit([Message("user", "same")])
    wait_results(runtime2)
    runtime2.submit([Message("user", "same")])
    results = wait_results(runtime2)
    runtime2.shutdown()
    assert not results[0].cached and len(provider2.requests) == 2


def test_job_system_validates_structured_output():
    good = MockProvider(reply='{"action": "rest", "duration": 60}')
    jobs = AIJobSystem(AIRuntime(FAST, good), validator=lambda payload: {"action": payload["action"]})
    seen = []
    jobs.submit([Message("user", "plan")], callback=seen.append)
    results = jobs.update()
    jobs.shutdown()
    assert results[0].ok and results[0].data["action"] == "rest"
    assert seen and seen[0].job_id == results[0].job_id

    bad = MockProvider(reply="not json at all")
    jobs = AIJobSystem(AIRuntime(FAST, bad), validator=lambda payload: payload)
    jobs.submit([Message("user", "plan")])
    results = jobs.update()
    jobs.shutdown()
    assert not results[0].ok and results[0].error.kind is ErrorKind.BAD_RESPONSE


def test_shutdown_is_terminal():
    runtime = AIRuntime(FAST, MockProvider())
    runtime.shutdown()
    with pytest.raises(AIError):
        runtime.submit([Message("user", "hi")])


def test_ollama_adapter_parses_chat_and_models():
    stub = Stub({
        ("POST", "/api/chat"): (200, {"model": "llama3", "message": {"role": "assistant", "content": "evening"},
                                     "prompt_eval_count": 11, "eval_count": 4, "done_reason": "stop"}),
        ("GET", "/api/tags"): (200, {"models": [{"name": "llama3"}, {"name": "qwen3"}]}),
    })
    try:
        provider = OllamaProvider(ProviderConfig(provider="ollama", model="llama3", endpoint=stub.url))
        response = provider.chat(ChatRequest.build("llama3", [Message("user", "hi")]))
        assert response.text == "evening"
        assert response.usage.prompt_tokens == 11 and response.usage.completion_tokens == 4
        assert provider.list_models() == ["llama3", "qwen3"]
        sent = json.loads(stub.requests[0][2])
        assert sent["stream"] is False
        assert sent["messages"] == [{"role": "user", "content": "hi"}]
    finally:
        stub.close()


def test_ollama_error_mapping():
    stub = Stub({("POST", "/api/chat"): (500, {"error": "boom"}),
                 ("GET", "/api/tags"): (401, {"error": "denied"})})
    try:
        provider = OllamaProvider(ProviderConfig(provider="ollama", model="m", endpoint=stub.url))
        with pytest.raises(ProviderError) as server:
            provider.chat(ChatRequest.build("m", [Message("user", "hi")]))
        assert server.value.kind is ErrorKind.SERVER and server.value.retryable
        with pytest.raises(ProviderError) as auth:
            provider.list_models()
        assert auth.value.kind is ErrorKind.AUTH and not auth.value.retryable
    finally:
        stub.close()


def test_ollama_malformed_payload_is_bad_response():
    stub = Stub({("POST", "/api/chat"): (200, "this is not json")})
    try:
        provider = OllamaProvider(ProviderConfig(provider="ollama", model="m", endpoint=stub.url))
        with pytest.raises(ProviderError) as exc:
            provider.chat(ChatRequest.build("m", [Message("user", "hi")]))
        assert exc.value.kind is ErrorKind.BAD_RESPONSE
    finally:
        stub.close()


def test_openai_adapter_and_key_redaction():
    import os
    os.environ["P3D_TEST_KEY"] = "sk-supersecret"
    stub = Stub({("POST", "/chat/completions"): (200, {
        "model": "gpt-test",
        "choices": [{"message": {"content": "hi there"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3},
    })})
    try:
        config = ProviderConfig(provider="openai", model="gpt-test", endpoint=stub.url,
                                api_key_env="P3D_TEST_KEY")
        provider = OpenAICompatibleProvider(config)
        response = provider.chat(ChatRequest.build("gpt-test", [Message("user", "hi")]))
        assert response.text == "hi there" and response.usage.total_tokens == 10
        assert "Authorization" in stub.requests[0][3] or "authorization" in {k.lower() for k in stub.requests[0][3]}
    finally:
        stub.close()
        os.environ.pop("P3D_TEST_KEY", None)

    leaky = Stub({("POST", "/chat/completions"): (401, {"error": "bad key sk-supersecret"})})
    try:
        config = ProviderConfig(provider="openai", model="m", endpoint=leaky.url,
                                api_key_env="P3D_TEST_KEY", allow_remote=True)
        provider = OpenAICompatibleProvider(config)
        os.environ["P3D_TEST_KEY"] = "sk-supersecret"
        try:
            with pytest.raises(ProviderError) as exc:
                provider.chat(ChatRequest.build("m", [Message("user", "hi")]))
            assert exc.value.kind is ErrorKind.AUTH
            assert "sk-supersecret" not in str(exc.value)
        finally:
            del os.environ["P3D_TEST_KEY"]
    finally:
        leaky.close()


def test_remote_provider_refused_by_default():
    provider = OllamaProvider(ProviderConfig(provider="ollama", model="m", endpoint="https://example.com"))
    with pytest.raises(AIError):
        provider.chat(ChatRequest.build("m", [Message("user", "hi")]))
