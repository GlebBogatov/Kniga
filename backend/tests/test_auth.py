from app.config import settings


def _login(client, provider_user_id="u1", **kw):
    r = client.post(
        "/api/auth/dev-login",
        json={"provider": "vk", "provider_user_id": provider_user_id, **kw},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _auth(data):
    return {"Authorization": f"Bearer {data['token']}"}


def test_dev_login_and_me(client):
    data = _login(client, email="a@b.ru", name="Аня")
    assert data["user"]["email"] == "a@b.ru"
    assert data["user"]["subscription"]["plan"] == "free"

    assert client.get("/api/auth/me").status_code == 401  # без токена

    me = client.get("/api/auth/me", headers=_auth(data))
    assert me.status_code == 200
    assert me.json()["name"] == "Аня"


def test_ui_mode_default_and_update(client):
    data = _login(client, provider_user_id="ui1")
    h = _auth(data)
    # По умолчанию — простой интерфейс.
    assert data["user"]["ui_mode"] == "simple"
    assert client.get("/api/auth/me", headers=h).json()["ui_mode"] == "simple"

    # Переключение на продвинутый сохраняется.
    r = client.patch("/api/auth/me", json={"ui_mode": "advanced"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["ui_mode"] == "advanced"
    assert client.get("/api/auth/me", headers=h).json()["ui_mode"] == "advanced"

    # Невалидное значение отклоняется.
    bad = client.patch("/api/auth/me", json={"ui_mode": "expert"}, headers=h)
    assert bad.status_code == 422


def test_login_provider_is_stub(client):
    r = client.get("/api/auth/login/vk")
    assert r.status_code == 200
    assert r.json()["stub"] is True
    assert client.get("/api/auth/login/unknown").status_code == 404


def test_dev_login_can_be_disabled(client):
    settings.allow_dev_login = False
    try:
        r = client.post(
            "/api/auth/dev-login",
            json={"provider": "vk", "provider_user_id": "x"},
        )
        assert r.status_code == 403
    finally:
        settings.allow_dev_login = True


def test_journal_scoped_to_user(client):
    user = _login(client, provider_user_id="u1")
    h = _auth(user)
    body = {"mode": "8", "question": "Мой вопрос сейчас?", "trigram_id": "qian"}

    client.post("/api/reading", json=body, headers=h)   # запись пользователя
    client.post("/api/reading", json=body)              # анонимная запись

    assert len(client.get("/api/journal", headers=h).json()) == 1
    assert len(client.get("/api/journal").json()) == 1


def test_cannot_delete_others_reading(client):
    a = _login(client, provider_user_id="a")
    b = _login(client, provider_user_id="b")
    body = {"mode": "8", "question": "Вопрос пользователя A?", "trigram_id": "qian"}
    rid = client.post("/api/reading", json=body, headers=_auth(a)).json()["reading_id"]

    # B не может удалить запись A
    assert client.delete(f"/api/journal/{rid}", headers=_auth(b)).status_code == 404
    # A может
    assert client.delete(f"/api/journal/{rid}", headers=_auth(a)).status_code == 200


def test_logout_invalidates_session(client):
    data = _login(client)
    h = _auth(data)
    assert client.get("/api/auth/me", headers=h).status_code == 200
    client.post("/api/auth/logout", headers=h)
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_delete_account_removes_data(client):
    data = _login(client, provider_user_id="u9")
    h = _auth(data)
    client.post(
        "/api/reading",
        json={"mode": "8", "question": "Вопрос удаляемого?", "trigram_id": "qian"},
        headers=h,
    )
    assert client.delete("/api/auth/account", headers=h).status_code == 200
    assert client.get("/api/auth/me", headers=h).status_code == 401
