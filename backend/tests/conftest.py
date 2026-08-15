import app.models  # noqa: F401  (регистрация моделей на Base)
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.services.llm import get_llm_service
from app.services.ratelimit import limiter

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
    """Замоканный LLM: возвращает форму по свойствам JSON-схемы."""

    def call_structured(self, prompt, schema, *, model, max_tokens):
        props = schema.get("properties", {})
        if "quality" in props:
            return {"quality": "good", "hint": "", "crisis": False}
        if "analysis_markdown" in props:
            return {"analysis_markdown": "# Анализ\nтекст"}
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


@pytest.fixture(autouse=True)
def _reset_state():
    settings.rate_limit_enabled = False
    settings.freemium_enabled = False
    limiter.reset()
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield
    settings.rate_limit_enabled = False
    settings.freemium_enabled = False
    limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session_factory():
    return TestSession
