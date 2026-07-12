from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    migration_database_url: str | None = None

    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"
    project_name: str = "AssetFlow API"
    api_v1_str: str = "/api"
    secret_key: str
    access_token_expire_minutes: int = 11520

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
