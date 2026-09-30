from functools import lru_cache
from typing import Optional
from pydantic import Field, AliasChoices
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

    # Embedding Model & Semantic Matching (Phase 7)
    embedding_model_name: str = "all-MiniLM-L6-v2"
    semantic_matching_enabled: bool = True
    semantic_high_threshold: float = 0.75
    semantic_medium_threshold: float = 0.55

    # Configurable Scoring Weights (Must sum to ~1.0, Phase 8)
    weight_rule_fit: float = Field(
        default=0.30,
        validation_alias=AliasChoices("weight_rule_fit", "rule_fit_weight", "rule_weight"),
        description="Weight for deterministic rule fit component",
    )
    weight_semantic_fit: float = Field(
        default=0.40,
        validation_alias=AliasChoices("weight_semantic_fit", "semantic_fit_weight", "semantic_weight"),
        description="Weight for semantic embedding fit component",
    )
    weight_experience_fit: float = Field(
        default=0.20,
        validation_alias=AliasChoices("weight_experience_fit", "experience_fit_weight", "experience_weight"),
        description="Weight for verifiable experience fit component",
    )
    weight_llm_fit: float = Field(
        default=0.10,
        validation_alias=AliasChoices("weight_llm_fit", "llm_fit_weight", "llm_weight"),
        description="Weight for LLM-supported fit component",
    )
    not_evaluable_policy: str = Field(
        default="exclude",
        description="Policy for handling not_evaluable requirements in score calculation ('exclude' or 'zero')",
    )

    @property
    def rule_fit_weight(self) -> float:
        return self.weight_rule_fit

    @property
    def semantic_fit_weight(self) -> float:
        return self.weight_semantic_fit

    @property
    def experience_fit_weight(self) -> float:
        return self.weight_experience_fit

    @property
    def llm_fit_weight(self) -> float:
        return self.weight_llm_fit

    # Privacy / Masked Mode Default
    default_masked_mode: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
