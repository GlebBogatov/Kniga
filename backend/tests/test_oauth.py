"""Тесты реального входа через Яндекс OAuth (сетевые вызовы замоканы)."""
from app.config import settings
from app.services import oauth

YANDEX_AUTHORIZE = "https://oauth.yandex.ru/authorize"


def _enable_yandex():
    settings.yandex_client_id = "test-id"
    settings.yandex_client_secret = "test-secret"
    settings.public_base_url = "https://test.local"


def _disable_yandex():
    settings.yandex_client_id = ""
    settings.yandex_client_secret = ""
    settings.public_base_url = ""


def test_yandex_start_disabled_redirects_error(client):
    _disable_yandex()
    r = client.get("/api/auth/oauth/yandex/start", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/#/auth-error"


def test_yandex_start_redirects_to_yandex(client):
    _enable_yandex()
    try:
        r = client.get("/api/auth/oauth/yandex/start", follow_redirects=False)
        assert r.status_code == 307
        loc = r.headers["location"]
        assert loc.startswith(YANDEX_AUTHORIZE)
        assert "client_id=test-id" in loc
        assert "state=" in loc
        assert "callback" in loc  # redirect_uri присутствует
    finally:
        _disable_yandex()


def test_yandex_callback_bad_state(client):
    r = client.get(
        "/api/auth/oauth/yandex/callback",
        params={"code": "x", "state": "nonexistent"},
        follow_redirects=False,
    )
    assert r.status_code == 307
    assert r.headers["location"] == "/#/auth-error"


def test_yandex_callback_creates_user(client, monkeypatch):
    _enable_yandex()
    try:
        monkeypatch.setattr(oauth, "exchange_code", lambda code: "access-tok")
        monkeypatch.setattr(
            oauth, "fetch_userinfo",
            lambda tok: {
                "id": "42", "login": "ivan",
                "real_name": "Иван Петров", "default_email": "ivan@ya.ru",
            },
        )
        state = oauth.create_state()
        r = client.get(
            "/api/auth/oauth/yandex/callback",
            params={"code": "good-code", "state": state},
            follow_redirects=False,
        )
        assert r.status_code == 307
        loc = r.headers["location"]
        assert loc.startswith("/#/auth-callback/")
        token = loc.rsplit("/", 1)[1]
        assert token

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        body = me.json()
        assert body["provider"] == "yandex"
        assert body["email"] == "ivan@ya.ru"
        assert body["name"] == "Иван Петров"
        assert body["ui_mode"] == "simple"

        # state одноразовый — повторный callback с ним не проходит
        r2 = client.get(
            "/api/auth/oauth/yandex/callback",
            params={"code": "good-code", "state": state},
            follow_redirects=False,
        )
        assert r2.headers["location"] == "/#/auth-error"
    finally:
        _disable_yandex()
