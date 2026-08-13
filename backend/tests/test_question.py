def test_question_check_returns_quality_and_crisis(client):
    r = client.post("/api/question/check", json={"question": "Стоит ли менять работу?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["quality"] in ("good", "vague", "yes_no_ok")
    assert isinstance(body["crisis"], bool)
    assert "hint" in body


def test_question_check_validates_length(client):
    r = client.post("/api/question/check", json={"question": ""})
    assert r.status_code == 422
