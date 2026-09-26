from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    clob_api_url: str = "https://clob.polymarket.com"
    request_timeout_seconds: float = 20.0
    default_market_limit: int = 50
    min_liquidity: float = 1000.0
    min_volume: float = 1000.0

    database_url: str = "sqlite+aiosqlite:///./polymarket.db"

    worker_interval_seconds: int = 900
    worker_max_research_per_cycle: int = 3
    min_research_interval_seconds: int = 3600
    resolution_concurrency: int = 10

    openai_api_key: str = ""
    admin_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    ai_max_output_tokens: int = 2500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_database(self):
        if self.app_env.lower() in {"production", "prod"} and self.database_url.startswith("sqlite"):
            raise ValueError("Production deployments require DATABASE_URL to point to PostgreSQL")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
