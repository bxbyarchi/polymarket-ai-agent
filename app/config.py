from functools import lru_cache

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

    openai_api_key: str = ""
    openai_model: str = "gpt-6-astra"
    ai_max_output_tokens: int = 2500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
