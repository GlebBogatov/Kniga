def test_list_trigrams(client):
    r = client.get("/api/trigrams")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 8
    assert all(isinstance(t["lines"], list) for t in data)


def test_get_trigram_and_404(client):
    assert client.get("/api/trigrams/li").json()["name"] == "Ли"
    assert client.get("/api/trigrams/nope").status_code == 404


def test_list_hexagrams(client):
    r = client.get("/api/hexagrams")
    assert r.status_code == 200
    assert len(r.json()) == 64


def test_get_hexagram_and_404(client):
    assert client.get("/api/hexagrams/63").json()["name"] == "Цзи цзи"
    assert client.get("/api/hexagrams/999").status_code == 404


def test_presets(client):
    r = client.get("/api/presets")
    assert r.status_code == 200
    assert len(r.json()) >= 1
    slug = r.json()[0]["slug"]
    assert client.get(f"/api/presets/{slug}").status_code == 200
    assert client.get("/api/presets/nope").status_code == 404


def test_presets_topic_filter(client):
    r = client.get("/api/presets", params={"topic": "career"})
    assert r.status_code == 200
    assert all(p["topic"] == "career" for p in r.json())


def test_reading_with_preset_slug(client):
    r = client.post("/api/reading", json={
        "mode": "8", "question": "Стоит ли менять работу?",
        "trigram_id": "qian", "preset_slug": "stoit-li-menyat-rabotu",
    })
    assert r.status_code == 200
