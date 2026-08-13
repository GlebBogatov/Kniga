from app.models import Reading


def test_reading_stream_emits_events_and_saves(client, session_factory):
    r = client.post("/api/reading/stream", json={
        "mode": "8", "question": "Вопрос про работу?", "trigram_id": "qian",
    })
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    body = r.text
    assert "event: delta" in body
    assert "event: done" in body
    with session_factory() as db:
        assert db.query(Reading).count() == 1


def test_reading_stream_invalid_mode_yields_error(client):
    # mode=8 без trigram_id: ошибка валидации ловится до стрима (422)
    r = client.post("/api/reading/stream", json={"mode": "8", "question": "достаточно длинный вопрос?"})
    assert r.status_code == 422
