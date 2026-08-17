"""Настройки приложения (pydantic-settings). Читаются из окружения / .env."""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Anthropic / LLM
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    outbound_proxy_url: str | None = None
    llm_provider: Literal["anthropic", "openrouter", "timeweb"] = "anthropic"
    openrouter_api_key: str | None = None

    # Timeweb AI Gateway (OpenAI-совместимый, оплата в рублях, доступ из РФ).
    timeweb_api_key: str = ""
    timeweb_base_url: str = "https://api.timeweb.ai/v1"

    # Модели (конфигурируемо, чтобы менять без правки логики)
    model_interpretation: str = "claude-sonnet-5"
    model_light: str = "claude-haiku-4-5"

    # Аккаунты / сессии
    # Заглушка входа вместо реального VK/Яндекс OAuth (внешние сервисы —
    # пока заглушки; реальные ключи подключаются позже).
    allow_dev_login: bool = True
    session_ttl_days: int = 30

    # Тарифы / лимиты (freemium). freemium_enabled выключается в тестах.
    freemium_enabled: bool = True
    free_daily_readings: int = 3

    # Платёжный провайдер — пока ЗАГЛУШКА (реальная ЮKassa подключается позже).
    payment_provider: str = "stub"          # "stub" | "yookassa"
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""

    # Прочее
    db_url: str = "sqlite:///./iching.db"
    cors_origins: str = "http://localhost:5173"
    rate_limit_enabled: bool = True
    max_body_bytes: int = 8192

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
