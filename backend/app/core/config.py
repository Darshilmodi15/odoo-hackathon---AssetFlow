# pyrefly: ignore [missing-import]
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

    # Compatibility properties for uppercase names used in earlier codebases
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def SECRET_KEY(self) -> str:
        return self.secret_key

    @property
    def PROJECT_NAME(self) -> str:
        return self.project_name

    @property
    def API_V1_STR(self) -> str:
        return self.api_v1_str

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.access_token_expire_minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
