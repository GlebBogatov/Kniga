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
    llm_provider: Literal["anthropic", "openrouter"] = "anthropic"
    openrouter_api_key: str | None = None

    # Модели (конфигурируемо, чтобы менять без правки логики)
    model_interpretation: str = "claude-sonnet-5"
    model_light: str = "claude-haiku-4-5"

    # Прочее
    db_url: str = "sqlite:///./iching.db"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
