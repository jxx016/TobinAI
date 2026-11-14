"""Runtime settings. Safe defaults keep every external provider mocked."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Environment-backed configuration.

    Live providers stay off until ``MOCK_EXTERNAL_SERVICES`` is false and the
    matching key is present. The chat model is selected separately: a key
    selects a real model, and no key selects the deterministic mock.
    """

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mock_external_services: bool = True
    database_url: str = "sqlite:///./var/lead_chase.db"
    checkpoint_database_url: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "lead-chase-agent"

    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    resend_api_key: str = ""
    resend_from_email: str = "outreach@example.com"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_whatsapp_from: str = ""

    calcom_api_key: str = ""
    calcom_api_url: str = "https://api.cal.com/v2"
    calcom_username: str = ""
    calcom_event_type_id: str = ""

    reflection_output_dir: str = "./var/reflection"
    followup_poll_seconds: int = 60
    nightly_reflection_hour: int = Field(default=2, ge=0, le=23)
    scheduler_enabled: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8080
    public_base_url: str = "http://127.0.0.1:8080"

    def resolved_database_url(self) -> str:
        return _resolve_sqlite(self.database_url)

    def resolved_checkpoint_url(self) -> str:
        explicit = (self.checkpoint_database_url or "").strip()
        if explicit:
            return explicit
        if self.database_url.startswith(("postgres://", "postgresql://", "postgresql+")):
            return self.database_url
        return ""

    def reflection_dir(self) -> Path:
        raw = Path(self.reflection_output_dir)
        path = raw if raw.is_absolute() else ROOT / raw
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def llm_provider(self) -> str:
        if self.openai_api_key.strip():
            return "openai"
        if self.anthropic_api_key.strip():
            return "anthropic"
        return "mock"


def _resolve_sqlite(url: str) -> str:
    prefix = "sqlite:///./"
    if url.startswith(prefix):
        path = (ROOT / url[len(prefix) :]).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + path.as_posix()
    return url


def apply_tracing(settings: Settings) -> None:
    """Mirror LangSmith flags into the env vars LangChain already reads."""

    os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.langchain_tracing_v2 else "false"
    if settings.langchain_api_key.strip():
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key.strip()
    if settings.langchain_project.strip():
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project.strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    apply_tracing(settings)
    return settings


def reset_settings() -> None:
    get_settings.cache_clear()
