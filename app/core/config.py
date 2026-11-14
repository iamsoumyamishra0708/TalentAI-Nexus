from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "TalentAI Agentic Recruitment"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database Endpoints
    DATABASE_URL: str
    QDRANT_URL: str
    REDIS_URL: str

    # External AI & Communication Keys
    LLM_API_KEY: str
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # Pydantic configuration to read from .env file automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Ignores extra variables in .env without crashing
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Creates a singleton instance of settings.
    @lru_cache ensures .env is read from disk only once at startup, saving memory and I/O.
    """
    return Settings()

settings = get_settings()