from app.config import settings

READING = {"mode": "8", "question": "Куда мне двигаться сейчас?", "trigram_id": "qian"}


def _login(client, uid="u1"):
    r = client.post("/api/auth/dev-login", json={"provider": "vk", "provider_user_id": uid})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _go_premium(client, h):
    pid = client.post(
        "/api/payments/checkout", json={"tariff_id": "premium_month"}, headers=h
    ).json()["payment_id"]
    client.post(f"/api/payments/dev-confirm/{pid}", headers=h)


def test_symbol_of_day_requires_login(client):
    assert client.get("/api/symbol-of-day").status_code == 401


def test_symbol_of_day_returns_symbol(client):
    # freemium выключен в тестах — доступно любому вошедшему
    h = _login(client)
    r = client.get("/api/symbol-of-day", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"]["kind"] == "trigram"
    assert body["reflection"]
    assert body["date"]


def test_symbol_of_day_premium_only(client):
    settings.freemium_enabled = True
    try:
        h = _login(client)
        assert client.get("/api/symbol-of-day", headers=h).status_code == 402
        _go_premium(client, h)
        assert client.get("/api/symbol-of-day", headers=h).status_code == 200
    finally:
        settings.freemium_enabled = False


def test_chat_limit_free_is_one(client):
    settings.freemium_enabled = True
    try:
        h = _login(client)
        rid = client.post("/api/reading", json=READING, headers=h).json()["reading_id"]
        r1 = client.post(f"/api/reading/{rid}/chat", json={"message": "А подробнее?"}, headers=h)
        assert r1.status_code == 200
        assert r1.json()["remaining"] == 0
        r2 = client.post(f"/api/reading/{rid}/chat", json={"message": "Ещё?"}, headers=h)
        assert r2.status_code == 400
    finally:
        settings.freemium_enabled = False


def test_chat_limit_premium_is_five(client):
    settings.freemium_enabled = True
    try:
        h = _login(client)
        _go_premium(client, h)
        rid = client.post("/api/reading", json=READING, headers=h).json()["reading_id"]
        for _ in range(5):
            assert client.post(
                f"/api/reading/{rid}/chat", json={"message": "?"}, headers=h
            ).status_code == 200
        assert client.post(
            f"/api/reading/{rid}/chat", json={"message": "?"}, headers=h
        ).status_code == 400
    finally:
        settings.freemium_enabled = False
