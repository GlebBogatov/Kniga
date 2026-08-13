from app.models import Reading


def _count_readings(session_factory) -> int:
    with session_factory() as db:
        return db.query(Reading).count()


def test_reading_mode_8_happy_path(client, session_factory):
    r = client.post("/api/reading", json={
        "mode": "8", "question": "Стоит ли менять работу?", "trigram_id": "qian",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"]["kind"] == "trigram"
    assert body["symbol"]["id"] == "qian"
    assert body["interpretation"] == "толкование"
    assert isinstance(body["reading_id"], int)
    assert _count_readings(session_factory) == 1


def test_reading_mode_64_happy_path(client):
    r = client.post("/api/reading", json={
        "mode": "64", "question": "Как сложится проект?", "lower_id": "li", "upper_id": "kan",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"]["kind"] == "hexagram"
    assert body["symbol"]["number"] == 63
    assert "lines_commentary" not in body


def test_reading_mode_coins_with_tosses(client):
    r = client.post("/api/reading", json={
        "mode": "coins", "question": "Что меня ждёт?", "tosses": [6, 6, 6, 6, 6, 6],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"]["number"] == 2
    assert body["symbol"]["secondary"]["number"] == 1
    assert body["symbol"]["changing_lines"] == [1, 2, 3, 4, 5, 6]
    assert body["lines_commentary"] == [{"line": 1, "text": "комментарий"}]


def test_reading_mode_coins_virtual_toss(client):
    r = client.post("/api/reading", json={
        "mode": "coins", "question": "Виртуальный бросок?", "tosses": None,
    })
    assert r.status_code == 200, r.text
    assert 1 <= r.json()["symbol"]["number"] <= 64


def test_reading_422_missing_trigram(client):
    r = client.post("/api/reading", json={"mode": "8", "question": "Достаточно длинный вопрос?"})
    assert r.status_code == 422


def test_reading_422_missing_upper(client):
    r = client.post("/api/reading", json={
        "mode": "64", "question": "Достаточно длинный вопрос?", "lower_id": "li",
    })
    assert r.status_code == 422


def test_reading_422_question_too_short(client):
    r = client.post("/api/reading", json={"mode": "8", "question": "ab", "trigram_id": "qian"})
    assert r.status_code == 422
