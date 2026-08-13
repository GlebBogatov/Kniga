import anthropic
import httpx
import pytest

from app.config import Settings
from app.services.llm import (
    AnthropicProvider,
    CircuitBreaker,
    LLMCallError,
    LLMService,
    LLMUnavailable,
    OpenRouterProvider,
    build_provider,
)


class FakeProvider:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def call_structured(self, prompt, schema, *, model, max_tokens):
        self.calls += 1
        return {"ok": True, "prompt": prompt}

    def call_text(self, system, messages, *, model, max_tokens):
        return "text"

    def stream_text(self, prompt, *, model, max_tokens):
        yield "chunk"


class FailingProvider:
    name = "failing"

    def __init__(self, exc):
        self._exc = exc
        self.calls = 0

    def call_structured(self, *a, **k):
        self.calls += 1
        raise self._exc

    def call_text(self, *a, **k):
        self.calls += 1
        raise self._exc

    def stream_text(self, *a, **k):
        raise self._exc
        yield  # pragma: no cover


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_call_structured_returns_validated_dict():
    svc = LLMService(FakeProvider())
    out = svc.call_structured("p", {"type": "object"}, model="m", max_tokens=10)
    assert out == {"ok": True, "prompt": "p"}


def test_breaker_opens_after_threshold_and_closes_after_reset():
    clock = Clock()
    b = CircuitBreaker(threshold=3, reset_seconds=60, time_func=clock)
    for _ in range(3):
        b.record_failure()
    assert b.is_open
    with pytest.raises(LLMUnavailable):
        b.before_call()
    clock.t = 61  # прошёл таймаут -> half-open
    b.before_call()  # не бросает
    b.record_success()
    assert not b.is_open


def test_network_failures_open_breaker_then_503():
    clock = Clock()
    breaker = CircuitBreaker(threshold=2, reset_seconds=60, time_func=clock)
    prov = FailingProvider(httpx.ConnectError("down"))
    svc = LLMService(prov, breaker, retries=2, sleep_func=lambda s: None)

    for _ in range(2):  # два неудачных вызова -> breaker открыт
        with pytest.raises(LLMCallError):
            svc.call_structured("p", {}, model="m", max_tokens=5)
    assert breaker.is_open

    calls_before = prov.calls
    with pytest.raises(LLMUnavailable):  # открыт -> 503, провайдер не вызывается
        svc.call_structured("p", {}, model="m", max_tokens=5)
    assert prov.calls == calls_before


def test_api_error_maps_to_call_error_without_retry():
    prov = FailingProvider(anthropic.BadRequestError(
        message="bad", response=httpx.Response(400, request=httpx.Request("POST", "http://x")), body=None,
    ))
    svc = LLMService(prov, retries=3, sleep_func=lambda s: None)
    with pytest.raises(LLMCallError):
        svc.call_text(None, [{"role": "user", "content": "x"}], model="m", max_tokens=5)
    assert prov.calls == 1  # API-ошибка не ретраится


def test_build_provider_switches_by_env():
    s_or = Settings(llm_provider="openrouter", openrouter_api_key="x")
    assert isinstance(build_provider(s_or), OpenRouterProvider)
    s_an = Settings(llm_provider="anthropic", anthropic_api_key="x")
    assert isinstance(build_provider(s_an), AnthropicProvider)


def test_anthropic_provider_passes_base_url_and_proxy(monkeypatch):
    captured: dict = {}
    sentinel = object()

    class FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    monkeypatch.setattr(anthropic, "DefaultHttpxClient", lambda **k: sentinel)

    AnthropicProvider(api_key="k", base_url="https://relay.example",
                      proxy_url="socks5://localhost:9050")
    assert captured["base_url"] == "https://relay.example"
    assert captured["api_key"] == "k"
    assert captured["http_client"] is sentinel

    AnthropicProvider(api_key="k", base_url="https://api", proxy_url=None)
    assert captured["http_client"] is None
