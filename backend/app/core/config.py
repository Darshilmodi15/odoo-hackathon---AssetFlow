from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "AssetFlow API"
    api_v1_str: str = "/api"
    secret_key: str = "temporary_development_secret_key_change_in_production"
    access_token_expire_minutes: int = 11520
    database_url: str = "postgresql://postgres:postgres@localhost:5432/assetflow"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
