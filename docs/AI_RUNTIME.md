# AI runtime

Status: **implemented (chat), optional, offline-first.** The engine never imports
a network module unless you construct an AI runtime.

## Design

```
game loop ──submit()──► AIRuntime (bounded pool) ──► Provider adapter ──► HTTP
   ▲                                                        │
   └────────── update() ── poll() ◄── results queue ◄───────┘
```

- `submit()` never blocks the caller and returns a job id.
- `update()` is called from the fixed step and drains finished results.
- Concurrency is capped by `max_concurrency`; the pending queue is capped by
  `queue_limit` and raises instead of growing without bound.
- Retries happen only for network, timeout, rate-limit and 5xx failures, with
  exponential backoff and jitter. Auth and validation errors fail immediately.
- Cancellation is cooperative. A blocking HTTP call cannot be interrupted, so a
  cancellation that arrives mid-flight discards the result.

## Providers

| Provider | Chat | Streaming | JSON mode | Tools | Models | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `mock` | yes | yes | yes | no | yes | yes |
| `ollama` | yes | no | yes | no | yes | yes |
| `openai` (compatible) | yes | no | yes | yes | yes | yes |

Unsupported capabilities are declared `False`, not silently faked.

## Safety

- API keys come from environment variables named by `api_key_env`, never from
  code or files.
- Secrets are redacted from error text before it can reach logs.
- Remote endpoints are refused unless `allow_remote=True`.
- Model output is untrusted: `AIJobSystem(validator=...)` parses and validates
  JSON before anything reaches game state.

## Example

```python
runtime = p3d.AIRuntime(p3d.ProviderConfig(provider="ollama", model="llama3"))
jobs = p3d.AIJobSystem(runtime)
jobs.submit([p3d.Message("user", "The ferry is late. React in one line.")])

def update(dt):
    for result in jobs.update():
        if result.ok:
            print(result.response.text)
```
