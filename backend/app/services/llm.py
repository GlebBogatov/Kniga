"""LLM-сервис: провайдер-абстракция, устойчивость к сбоям (ретраи + circuit
breaker), structured output. Готов к трём каналам доступа без правки логики.

Ошибки наружу:
  - LLMUnavailable — открыт circuit breaker -> HTTP 503;
  - LLMCallError   — вызов не удался (после ретраев / API-ошибка) -> HTTP 502.
"""
import json
import logging
import time
from collections.abc import Callable, Iterator
from typing import Protocol, runtime_checkable

import anthropic
import httpx

logger = logging.getLogger("iching.llm")


class LLMError(Exception):
    pass


class LLMUnavailable(LLMError):
    """Circuit breaker открыт — канал временно недоступен (503)."""


class LLMCallError(LLMError):
    """Вызов LLM не удался (502)."""


# Сетевые ошибки — на них делаем ретраи и считаем сбои breaker'а.
_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
)


# --- Провайдеры ---


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def call_structured(self, prompt: str, schema: dict, *, model: str, max_tokens: int) -> dict: ...
    def call_text(self, system: str | None, messages: list, *, model: str, max_tokens: int) -> str: ...
    def stream_text(self, prompt: str, *, model: str, max_tokens: int) -> Iterator[str]: ...


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, *, api_key: str, base_url: str, proxy_url: str | None = None):
        http_client = (
            anthropic.DefaultHttpxClient(proxy=proxy_url) if proxy_url else None
        )
        self._client = anthropic.Anthropic(
            api_key=api_key, base_url=base_url, http_client=http_client, timeout=120
        )

    @staticmethod
    def _text(resp) -> str:
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    def call_structured(self, prompt, schema, *, model, max_tokens) -> dict:
        resp = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        return json.loads(self._text(resp))

    def call_text(self, system, messages, *, model, max_tokens) -> str:
        kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        return self._text(self._client.messages.create(**kwargs))

    def stream_text(self, prompt, *, model, max_tokens) -> Iterator[str]:
        with self._client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            yield from stream.text_stream


def _parse_json(text: str) -> dict:
    """Разбор JSON из ответа модели: чистый JSON либо в ```-ограждении.

    Timeweb/OpenRouter при json_schema возвращают чистый JSON, но некоторые
    модели/режимы оборачивают в ```json — разбираем защитно.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip()
    i, j = text.find("{"), text.rfind("}")
    if i != -1 and j > i:
        return json.loads(text[i : j + 1])
    return json.loads(text)  # бросит понятную ошибку


class OpenAICompatibleProvider:
    """OpenAI-совместимый провайдер (OpenRouter, Timeweb AI Gateway и т.п.).

    base_url — корень API (например https://api.timeweb.ai/v1); к нему
    добавляется /chat/completions. model_prefix подставляется, если в имени
    модели нет '/', — так `claude-sonnet-5` -> `anthropic/claude-sonnet-5`.
    """

    def __init__(self, *, api_key: str, base_url: str, name: str = "openai-compat",
                 model_prefix: str = "anthropic/", proxy_url: str | None = None):
        self.name = name
        self._api_key = api_key
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._prefix = model_prefix
        # 120с: тяжёлые ответы (монеты с изменяющимися линиями) на медленном
        # хостинге через шлюз могут генерироваться дольше 60с.
        self._http = httpx.Client(proxy=proxy_url, timeout=120) if proxy_url else httpx.Client(timeout=120)

    def _model(self, model: str) -> str:
        return model if "/" in model else f"{self._prefix}{model}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def call_structured(self, prompt, schema, *, model, max_tokens) -> dict:
        payload = {
            "model": self._model(model),
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "result", "strict": True, "schema": schema},
            },
        }
        r = self._http.post(self._url, headers=self._headers(), json=payload)
        r.raise_for_status()
        return _parse_json(r.json()["choices"][0]["message"]["content"])

    def call_text(self, system, messages, *, model, max_tokens) -> str:
        msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
        payload = {"model": self._model(model), "max_tokens": max_tokens, "messages": msgs}
        r = self._http.post(self._url, headers=self._headers(), json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def stream_text(self, prompt, *, model, max_tokens) -> Iterator[str]:
        payload = {
            "model": self._model(model),
            "max_tokens": max_tokens,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }
        with self._http.stream("POST", self._url, headers=self._headers(), json=payload) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta:
                    yield delta


class OpenRouterProvider(OpenAICompatibleProvider):
    """Запасной канал (OpenRouter, OpenAI-совместимый)."""

    def __init__(self, *, api_key: str, proxy_url: str | None = None):
        super().__init__(api_key=api_key, base_url="https://openrouter.ai/api/v1",
                         name="openrouter", model_prefix="anthropic/", proxy_url=proxy_url)


# --- Circuit breaker ---


class CircuitBreaker:
    def __init__(self, threshold: int = 5, reset_seconds: float = 60.0,
                 time_func: Callable[[], float] = time.monotonic):
        self._threshold = threshold
        self._reset = reset_seconds
        self._time = time_func
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        return self._opened_at is not None and (self._time() - self._opened_at) < self._reset

    def before_call(self) -> None:
        if self.is_open:
            raise LLMUnavailable("circuit breaker open")

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._time()


# --- Сервис ---


class LLMService:
    def __init__(self, provider: LLMProvider, breaker: CircuitBreaker | None = None, *,
                 retries: int = 3, backoff_base: float = 1.0,
                 sleep_func: Callable[[float], None] = time.sleep):
        self._provider = provider
        self._breaker = breaker or CircuitBreaker()
        self._retries = retries
        self._backoff = backoff_base
        self._sleep = sleep_func

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def _guarded(self, fn: Callable, *args, **kwargs):
        self._breaker.before_call()
        last_exc: Exception | None = None
        for attempt in range(self._retries):
            try:
                result = fn(*args, **kwargs)
            except _NETWORK_ERRORS as exc:
                last_exc = exc
                logger.warning("LLM network error (attempt %d/%d): %s",
                               attempt + 1, self._retries, type(exc).__name__)
                if attempt + 1 < self._retries:
                    self._sleep(self._backoff * (2 ** attempt))
                continue
            except anthropic.APIError as exc:
                logger.warning("LLM API error: %s", type(exc).__name__)
                raise LLMCallError(str(exc)) from exc
            except Exception as exc:  # прочие ошибки провайдера (в т.ч. OpenRouter)
                raise LLMCallError(str(exc)) from exc
            else:
                self._breaker.record_success()
                return result
        self._breaker.record_failure()
        raise LLMCallError("network failure after retries") from last_exc

    def call_structured(self, prompt: str, schema: dict, *, model: str, max_tokens: int) -> dict:
        return self._guarded(self._provider.call_structured, prompt, schema,
                             model=model, max_tokens=max_tokens)

    def call_text(self, system: str | None, messages: list, *, model: str, max_tokens: int) -> str:
        return self._guarded(self._provider.call_text, system, messages,
                             model=model, max_tokens=max_tokens)

    def stream_text(self, prompt: str, *, model: str, max_tokens: int) -> Iterator[str]:
        self._breaker.before_call()
        try:
            yield from self._provider.stream_text(prompt, model=model, max_tokens=max_tokens)
        except _NETWORK_ERRORS as exc:
            self._breaker.record_failure()
            raise LLMCallError(str(exc)) from exc
        except anthropic.APIError as exc:
            raise LLMCallError(str(exc)) from exc
        except Exception as exc:
            raise LLMCallError(str(exc)) from exc
        else:
            self._breaker.record_success()


# --- Фабрика и синглтон ---


def build_provider(settings) -> LLMProvider:
    if settings.llm_provider == "openrouter":
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key or "",
            proxy_url=settings.outbound_proxy_url,
        )
    if settings.llm_provider == "timeweb":
        return OpenAICompatibleProvider(
            api_key=settings.timeweb_api_key or "",
            base_url=settings.timeweb_base_url,
            name="timeweb",
            model_prefix="anthropic/",
            proxy_url=settings.outbound_proxy_url,
        )
    return AnthropicProvider(
        api_key=settings.anthropic_api_key,
        base_url=settings.anthropic_base_url,
        proxy_url=settings.outbound_proxy_url,
    )


_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _service
    if _service is None:
        from ..config import settings

        _service = LLMService(build_provider(settings))
    return _service
