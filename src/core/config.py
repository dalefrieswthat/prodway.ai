"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Database
    database_url: str = Field(default="postgresql+asyncpg://localhost/context_engine")

    # Vector Store
    pinecone_api_key: str = Field(default="")
    pinecone_environment: str = Field(default="us-east-1")
    pinecone_index: str = Field(default="context-engine")

    # AI Providers
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")  # For embeddings

    # Slack
    slack_bot_token: str = Field(default="")
    slack_signing_secret: str = Field(default="")
    slack_app_token: str = Field(default="")

    # GitHub
    github_token: str = Field(default="")
    github_webhook_secret: str = Field(default="")

    # Gmail
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    google_refresh_token: str = Field(default="")

    # Notion
    notion_api_key: str = Field(default="")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Context Paths
    cursor_context_paths: str = Field(default="")

    @property
    def context_paths(self) -> list[Path]:
        """Parse comma-separated context paths into Path objects."""
        if not self.cursor_context_paths:
            return []
        return [Path(p.strip()) for p in self.cursor_context_paths.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
