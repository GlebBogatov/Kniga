def _login(client, uid, role=None):
    body = {"provider": "vk", "provider_user_id": uid}
    if role:
        body["role"] = role
    return client.post("/api/auth/dev-login", json=body).json()


def _h(data):
    return {"Authorization": f"Bearer {data['token']}"}


def test_cms_requires_editor(client):
    user = _login(client, "u1")
    assert client.get("/api/cms/content").status_code == 401
    assert client.get("/api/cms/content", headers=_h(user)).status_code == 403


def test_list_has_defaults(client):
    ed = _login(client, "tanya", role="editor")
    items = client.get("/api/cms/content", headers=_h(ed)).json()
    keys = [i["key"] for i in items]
    assert "safety" in keys and "qc_good" in keys
    safety = [i for i in items if i["key"] == "safety"][0]
    assert safety["published"] is None
    assert "специалист" in safety["effective"].lower()


def test_draft_publish_affects_generation(client):
    ed = _login(client, "tanya", role="editor")
    h = _h(ed)

    # правим критерий «хороший вопрос» и публикуем
    client.put(
        "/api/cms/content/qc_good",
        json={"value": "МАРКЕР-ТАНИ конкретный"},
        headers=h,
    )
    # предпросмотр берёт черновик
    prev = client.post("/api/cms/preview", json={"question": "Тест?"}, headers=h).json()
    assert "МАРКЕР-ТАНИ" in prev["question_check_prompt"]

    client.post("/api/cms/content/qc_good/publish", headers=h)
    # публичный эффективный контент обновился
    eff = client.get("/api/content").json()
    assert eff["qc_good"] == "МАРКЕР-ТАНИ конкретный"


def test_versions_and_restore(client):
    ed = _login(client, "tanya", role="editor")
    h = _h(ed)

    client.put("/api/cms/content/tone", json={"value": "Версия 1"}, headers=h)
    client.post("/api/cms/content/tone/publish", headers=h)
    client.put("/api/cms/content/tone", json={"value": "Версия 2"}, headers=h)
    client.post("/api/cms/content/tone/publish", headers=h)

    vers = client.get("/api/cms/content/tone/versions", headers=h).json()
    assert len(vers) == 2
    # восстановить самую старую версию в черновик
    oldest = vers[-1]["id"]
    client.post(f"/api/cms/content/tone/restore/{oldest}", headers=h)
    items = client.get("/api/cms/content", headers=h).json()
    tone = [i for i in items if i["key"] == "tone"][0]
    assert tone["draft"] == "Версия 1"


def test_unknown_key_404(client):
    ed = _login(client, "tanya", role="editor")
    r = client.put("/api/cms/content/nope", json={"value": "x"}, headers=_h(ed))
    assert r.status_code == 404
