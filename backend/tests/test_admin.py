def _login(client, uid, role=None):
    body = {"provider": "vk", "provider_user_id": uid, "email": f"{uid}@ex.ru"}
    if role:
        body["role"] = role
    r = client.post("/api/auth/dev-login", json=body)
    return r.json()


def _h(data):
    return {"Authorization": f"Bearer {data['token']}"}


def test_admin_required(client):
    user = _login(client, "u1")
    assert client.get("/api/admin/metrics").status_code == 401
    assert client.get("/api/admin/metrics", headers=_h(user)).status_code == 403


def test_metrics_and_users(client):
    admin = _login(client, "boss", role="admin")
    _login(client, "u1")
    _login(client, "u2")

    m = client.get("/api/admin/metrics", headers=_h(admin)).json()
    assert m["users_total"] == 3

    users = client.get("/api/admin/users", headers=_h(admin)).json()
    assert len(users) == 3
    found = client.get("/api/admin/users?query=u1", headers=_h(admin)).json()
    assert len(found) == 1 and found[0]["email"] == "u1@ex.ru"


def test_block_invalidates_session(client):
    admin = _login(client, "boss", role="admin")
    victim = _login(client, "v")
    vid = victim["user"]["id"]

    assert client.get("/api/auth/me", headers=_h(victim)).status_code == 200
    client.post(f"/api/admin/users/{vid}/block", headers=_h(admin))
    assert client.get("/api/auth/me", headers=_h(victim)).status_code == 401

    client.post(f"/api/admin/users/{vid}/unblock", headers=_h(admin))
    # новая сессия после разблокировки работает
    again = _login(client, "v")
    assert client.get("/api/auth/me", headers=_h(again)).status_code == 200


def test_grant_and_set_free(client):
    admin = _login(client, "boss", role="admin")
    user = _login(client, "u1")
    uid = user["user"]["id"]

    r = client.post(
        f"/api/admin/users/{uid}/grant",
        json={"tariff_id": "premium_year"},
        headers=_h(admin),
    ).json()
    assert r["subscription"]["plan"] == "premium"

    r2 = client.post(f"/api/admin/users/{uid}/set-free", headers=_h(admin)).json()
    assert r2["subscription"]["plan"] == "free"


def test_refund(client):
    admin = _login(client, "boss", role="admin")
    user = _login(client, "u1")
    uid = user["user"]["id"]
    pid = client.post(
        "/api/payments/checkout", json={"tariff_id": "premium_month"}, headers=_h(user)
    ).json()["payment_id"]
    client.post(f"/api/payments/dev-confirm/{pid}", headers=_h(user))

    r = client.post(f"/api/admin/users/{uid}/refund/{pid}", headers=_h(admin))
    assert r.status_code == 200
    assert r.json()["status"] == "refunded"
