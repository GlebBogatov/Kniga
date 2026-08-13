from app.config import settings
from app.services.ratelimit import limiter


def test_reading_rate_limited_after_hourly_limit(client):
    settings.rate_limit_enabled = True
    limiter.reset()
    payload = {"mode": "8", "question": "Стоит ли менять работу?", "trigram_id": "qian"}

    codes = [client.post("/api/reading", json=payload).status_code for _ in range(11)]

    assert codes[:10] == [200] * 10  # лимит 10/час
    assert codes[10] == 429


def test_body_size_limit(client):
    settings.rate_limit_enabled = False
    big = "x" * 9000
    r = client.post("/api/reading", json={"mode": "8", "question": big, "trigram_id": "qian"})
    assert r.status_code == 413
