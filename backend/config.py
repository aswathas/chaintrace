"""Settings loader — single source of truth for all env vars."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AI
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"

    # Blockchain data
    covalent_api_key: str = ""
    alchemy_api_key: str = ""
    etherscan_keys: List[str] = []
    arkham_api_key: str = ""

    # Databases
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_password: str = "forensic"
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql+asyncpg://forensic:forensic@localhost:5432/forensic"

    # Alerts
    discord_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    alchemy_webhook_auth_token: str = ""
    moralis_api_key: str = ""

    @field_validator("etherscan_keys", mode="before")
    @classmethod
    def split_comma(cls, v: object) -> List[str]:
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v  # type: ignore[return-value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
