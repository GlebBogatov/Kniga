from app.config import settings

READING = {"mode": "8", "question": "Вопрос дня сейчас?", "trigram_id": "qian"}


def _login(client, uid="u1"):
    r = client.post(
        "/api/auth/dev-login",
        json={"provider": "vk", "provider_user_id": uid, "email": "u@ex.ru"},
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _go_premium(client, headers, tariff="premium_month"):
    pid = client.post(
        "/api/payments/checkout", json={"tariff_id": tariff}, headers=headers
    ).json()["payment_id"]
    return client.post(f"/api/payments/dev-confirm/{pid}", headers=headers)


def test_list_tariffs(client):
    r = client.get("/api/tariffs")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert "premium_month" in ids and "premium_year" in ids


def test_checkout_and_confirm(client):
    h = _login(client)
    r = _go_premium(client, h)
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["subscription"]["plan"] == "premium"
    assert user["subscription"]["auto_renew"] is True
    assert user["subscription"]["current_period_end"] is not None
    assert "заглушка" in r.json()["payment"]["receipt"].lower()


def test_checkout_requires_auth(client):
    assert client.post(
        "/api/payments/checkout", json={"tariff_id": "premium_month"}
    ).status_code == 401


def test_cancel_autorenew(client):
    h = _login(client)
    _go_premium(client, h)
    r = client.post("/api/subscription/cancel", headers=h)
    assert r.status_code == 200
    assert r.json()["subscription"]["auto_renew"] is False
    assert r.json()["subscription"]["plan"] == "premium"  # доступ до конца периода


def test_free_daily_limit(client):
    settings.freemium_enabled = True
    settings.free_daily_readings = 2
    try:
        h = _login(client)
        assert client.post("/api/reading", json=READING, headers=h).status_code == 200
        assert client.post("/api/reading", json=READING, headers=h).status_code == 200
        r = client.post("/api/reading", json=READING, headers=h)
        assert r.status_code == 402
    finally:
        settings.freemium_enabled = False
        settings.free_daily_readings = 3


def test_premium_bypasses_limit(client):
    settings.freemium_enabled = True
    settings.free_daily_readings = 1
    try:
        h = _login(client)
        _go_premium(client, h)
        for _ in range(3):
            assert client.post("/api/reading", json=READING, headers=h).status_code == 200
    finally:
        settings.freemium_enabled = False
        settings.free_daily_readings = 3


def test_analyze_requires_premium(client):
    settings.freemium_enabled = True
    try:
        h = _login(client)
        client.post("/api/reading", json=READING, headers=h)
        client.post("/api/reading", json=READING, headers=h)
        assert client.post("/api/journal/analyze", headers=h).status_code == 402

        _go_premium(client, h)
        assert client.post("/api/journal/analyze", headers=h).status_code == 200
    finally:
        settings.freemium_enabled = False


def test_webhook_confirms_payment(client):
    h = _login(client)
    checkout = client.post(
        "/api/payments/checkout", json={"tariff_id": "premium_month"}, headers=h
    ).json()
    # достаём provider_payment_id через список платежей
    pid = checkout["payment_id"]
    payment = [p for p in client.get("/api/payments", headers=h).json() if p["id"] == pid][0]
    assert payment["status"] == "pending"

    # вебхук провайдера (заглушка формы ЮKassa)
    from app.models import Payment
    from tests.conftest import TestSession

    with TestSession() as db:
        prov_id = db.get(Payment, pid).provider_payment_id
    r = client.post(
        "/api/payments/webhook",
        json={"event": "payment.succeeded", "object": {"id": prov_id}},
    )
    assert r.status_code == 200
    me = client.get("/api/auth/me", headers=h).json()
    assert me["subscription"]["plan"] == "premium"
