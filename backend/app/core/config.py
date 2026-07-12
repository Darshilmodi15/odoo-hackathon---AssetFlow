from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AssetFlow API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "temporary_development_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/assetflow"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
