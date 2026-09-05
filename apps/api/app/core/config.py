"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Prodway API settings.

    DATABASE_URL uses SQLAlchemy's psycopg3 driver scheme, e.g.
    postgresql+psycopg://user:pass@host:5432/dbname
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://prodway:prodway@localhost:5433/prodway"
    environment: str = "development"


settings = Settings()
