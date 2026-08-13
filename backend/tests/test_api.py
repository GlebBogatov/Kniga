import app.models  # noqa: F401  (регистрация моделей на Base)
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Reading
from app.services.llm import get_llm_service

# Изолированная in-memory БД, общая между соединениями (StaticPool).
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


def _override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


class FakeLLM:
    def call_structured(self, prompt, schema, *, model, max_tokens):
        return {
            "interpretation": "толкование",
            "advice": "совет",
            "caution": "осторожно",
            "next_step": "первый шаг",
            "lines_commentary": [{"line": 1, "text": "комментарий"}],
        }

    def call_text(self, system, messages, *, model, max_tokens):
        return "ответ"

    def stream_text(self, prompt, *, model, max_tokens):
        yield "ответ"


app.dependency_overrides[get_db] = _override_db
app.dependency_overrides[get_llm_service] = lambda: FakeLLM()

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db():
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


def _count_readings() -> int:
    with TestSession() as db:
        return db.query(Reading).count()


def test_reading_mode_8_happy_path():
    r = client.post("/api/reading", json={
        "mode": "8", "question": "Стоит ли менять работу?", "trigram_id": "qian",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"]["kind"] == "trigram"
    assert body["symbol"]["id"] == "qian"
    assert body["interpretation"] == "толкование"
    assert isinstance(body["reading_id"], int)
    assert _count_readings() == 1


def test_reading_mode_64_happy_path():
    r = client.post("/api/reading", json={
        "mode": "64", "question": "Как сложится проект?", "lower_id": "li", "upper_id": "kan",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"]["kind"] == "hexagram"
    assert body["symbol"]["number"] == 63
    assert "lines_commentary" not in body


def test_reading_mode_coins_with_tosses():
    r = client.post("/api/reading", json={
        "mode": "coins", "question": "Что меня ждёт?", "tosses": [6, 6, 6, 6, 6, 6],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"]["kind"] == "hexagram"
    assert body["symbol"]["number"] == 2
    assert body["symbol"]["secondary"]["number"] == 1
    assert body["symbol"]["changing_lines"] == [1, 2, 3, 4, 5, 6]
    assert body["lines_commentary"] == [{"line": 1, "text": "комментарий"}]


def test_reading_mode_coins_virtual_toss():
    r = client.post("/api/reading", json={
        "mode": "coins", "question": "Виртуальный бросок?", "tosses": None,
    })
    assert r.status_code == 200, r.text
    assert 1 <= r.json()["symbol"]["number"] <= 64


def test_reading_422_missing_trigram():
    r = client.post("/api/reading", json={"mode": "8", "question": "Достаточно длинный вопрос?"})
    assert r.status_code == 422


def test_reading_422_missing_upper():
    r = client.post("/api/reading", json={
        "mode": "64", "question": "Достаточно длинный вопрос?", "lower_id": "li",
    })
    assert r.status_code == 422


def test_reading_422_question_too_short():
    r = client.post("/api/reading", json={"mode": "8", "question": "ab", "trigram_id": "qian"})
    assert r.status_code == 422
