from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration managed via Pydantic BaseSettings and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    app_name: str = "P_101 LLM-Based Resume Screening System"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "dev-secret-key-p101-local-only"

    # Database
    database_url: str = "sqlite:///./resume_screening.db"

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    # LLM Provider Configuration
    llm_provider: str = "mock"
    llm_api_key: Optional[str] = None
    llm_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.2

    # Embedding Model
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Configurable Scoring Weights (Must sum to ~1.0)
    weight_rule_fit: float = 0.30
    weight_semantic_fit: float = 0.40
    weight_experience_fit: float = 0.20
    weight_llm_fit: float = 0.10

    # Privacy / Masked Mode Default
    default_masked_mode: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
