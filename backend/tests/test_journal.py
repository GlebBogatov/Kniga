def _make_reading(client):
    return client.post("/api/reading", json={
        "mode": "8", "question": "Вопрос про работу?", "trigram_id": "qian",
    })


def test_journal_lists_after_reading(client):
    _make_reading(client)
    r = client.get("/api/journal")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["symbol_label"].startswith("Триграмма")
    assert data[0]["question"] == "Вопрос про работу?"


def test_journal_empty_initially(client):
    r = client.get("/api/journal")
    assert r.status_code == 200
    assert r.json() == []


def test_delete_entry(client):
    _make_reading(client)
    rid = client.get("/api/journal").json()[0]["id"]
    assert client.delete(f"/api/journal/{rid}").status_code == 200
    assert client.get("/api/journal").json() == []


def test_delete_missing_returns_404(client):
    assert client.delete("/api/journal/999").status_code == 404


def test_analyze_needs_two_entries(client):
    _make_reading(client)
    r = client.post("/api/journal/analyze")
    assert r.status_code == 400


def test_analyze_ok_with_two(client):
    _make_reading(client)
    _make_reading(client)
    r = client.post("/api/journal/analyze")
    assert r.status_code == 200
    assert "analysis_markdown" in r.json()
