def _editor(client):
    r = client.post(
        "/api/auth/dev-login",
        json={"provider": "vk", "provider_user_id": "tanya", "role": "editor"},
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_public_presets_default_when_empty(client):
    r = client.get("/api/presets")
    assert r.status_code == 200
    assert len(r.json()) == 5  # стартовый набор из кода


def test_editor_requires_role(client):
    user = client.post(
        "/api/auth/dev-login", json={"provider": "vk", "provider_user_id": "u1"}
    ).json()
    h = {"Authorization": f"Bearer {user['token']}"}
    assert client.get("/api/cms/presets").status_code == 401
    assert client.get("/api/cms/presets", headers=h).status_code == 403


def test_list_seeds_db(client):
    h = _editor(client)
    items = client.get("/api/cms/presets", headers=h).json()
    assert len(items) == 5
    assert all("id" in i for i in items)


def test_create_update_delete_preset(client):
    h = _editor(client)
    client.get("/api/cms/presets", headers=h)  # seed

    created = client.post(
        "/api/cms/presets",
        json={
            "title": "Новый вопрос Тани",
            "subtitle": "тест",
            "question_template": "Мой шаблон вопроса?",
            "prompt_focus": "особый фокус",
            "topic": "self",
        },
        headers=h,
    ).json()
    slug = created["slug"]
    assert created["title"] == "Новый вопрос Тани"

    # появился в публичном списке
    slugs = [p["slug"] for p in client.get("/api/presets").json()]
    assert slug in slugs
    assert client.get(f"/api/presets/{slug}").json()["prompt_focus"] == "особый фокус"

    # деактивация убирает из публичного списка
    client.put(f"/api/cms/presets/{created['id']}", json={"is_active": False}, headers=h)
    assert slug not in [p["slug"] for p in client.get("/api/presets").json()]

    # удаление
    assert client.delete(f"/api/cms/presets/{created['id']}", headers=h).status_code == 200
    assert client.get(f"/api/presets/{slug}").status_code == 404


def test_reading_uses_custom_preset_focus(client):
    h = _editor(client)
    created = client.post(
        "/api/cms/presets",
        json={"title": "Фокус-тест", "prompt_focus": "МАРКЕР-ФОКУСА", "topic": "self"},
        headers=h,
    ).json()
    # гадание с этим пресетом сохраняется (focus влияет на промпт, проверяем факт успеха)
    r = client.post(
        "/api/reading",
        json={
            "mode": "8",
            "question": "Куда двигаться?",
            "trigram_id": "qian",
            "preset_slug": created["slug"],
        },
        headers=h,
    )
    assert r.status_code == 200
