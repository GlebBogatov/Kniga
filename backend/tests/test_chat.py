def _reading_id(client) -> int:
    client.post("/api/reading", json={
        "mode": "8", "question": "Вопрос про работу?", "trigram_id": "qian",
    })
    return client.get("/api/journal").json()[0]["id"]


def test_chat_reply_and_remaining(client):
    rid = _reading_id(client)
    r = client.post(f"/api/reading/{rid}/chat", json={"message": "Уточните, пожалуйста"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == "ответ"       # FakeLLM.call_text
    assert body["remaining"] == 4


def test_chat_limit_on_sixth(client):
    rid = _reading_id(client)
    for _ in range(5):
        assert client.post(f"/api/reading/{rid}/chat", json={"message": "ещё"}).status_code == 200
    r = client.post(f"/api/reading/{rid}/chat", json={"message": "шестой"})
    assert r.status_code == 400


def test_chat_missing_reading_404(client):
    r = client.post("/api/reading/999/chat", json={"message": "вопрос"})
    assert r.status_code == 404
