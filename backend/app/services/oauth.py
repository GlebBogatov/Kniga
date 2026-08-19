"""Реальный вход через Яндекс OAuth 2.0 (Authorization Code Flow).

Поток:
  1) /auth/oauth/yandex/start — редирект на Яндекс с одноразовым `state` (CSRF).
  2) Яндекс возвращает `code` на redirect_uri (наш callback).
  3) callback: проверяем `state`, меняем `code` на access_token, тянем профиль,
     заводим/находим пользователя, открываем сессию, редиректим в SPA с токеном.

Секреты (client_id/secret) берутся из настроек (env) — в код не зашиты.
"""
import secrets
import time
from urllib.parse import urlencode

import httpx

from ..config import settings

AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"
USERINFO_URL = "https://login.yandex.ru/info"

_STATE_TTL = 600  # секунд жизни одноразового state
_states: dict[str, float] = {}


def _sweep(now: float) -> None:
    for s in [s for s, exp in _states.items() if exp < now]:
        _states.pop(s, None)


def create_state() -> str:
    now = time.time()
    _sweep(now)
    state = secrets.token_urlsafe(24)
    _states[state] = now + _STATE_TTL
    return state


def verify_state(state: str) -> bool:
    """Одноразовая проверка: валиден и не истёк (после проверки удаляется)."""
    exp = _states.pop(state, None)
    return exp is not None and exp >= time.time()


def authorize_url(state: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.yandex_client_id,
            "redirect_uri": settings.yandex_redirect,
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def exchange_code(code: str) -> str:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.yandex_client_id,
        "client_secret": settings.yandex_client_secret,
    }
    with httpx.Client(timeout=15) as client:
        resp = client.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]


def fetch_userinfo(access_token: str) -> dict:
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            USERINFO_URL,
            params={"format": "json"},
            headers={"Authorization": f"OAuth {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


def profile_to_user(info: dict) -> dict:
    """Свести профиль Яндекса к нашим полям (id/email/name)."""
    name = info.get("real_name") or info.get("display_name") or info.get("login")
    email = info.get("default_email")
    if not email:
        emails = info.get("emails") or []
        email = emails[0] if emails else None
    return {"provider_user_id": str(info["id"]), "email": email, "name": name}
