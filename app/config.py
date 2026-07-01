import logging
import os
from typing import Any, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # FastAPI Configurations
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # AI Configurations
    LLM_PROVIDER: str = Field(default="gemini", description="LLM provider: gemini or openai")
    EMBEDDING_TYPE: str = Field(default="gemini", description="Embedding type: gemini or local")

    # Model Configurations
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # RAG Settings
    CONFIDENCE_THRESHOLD: float = 0.5

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    CATALOG_PATH: str = os.path.join(DATA_DIR, "shl_catalog.json")
    FAISS_INDEX_PATH: str = os.path.join(DATA_DIR, "faiss.index")

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "enable", "enabled"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "disable", "disabled", ""}:
                return False
        logger.warning("Invalid DEBUG value %r. Falling back to True.", value)
        return True

    def validate_keys(self) -> None:
        """Validates that keys for the selected provider are present."""
        if self.LLM_PROVIDER.lower() == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is set to 'gemini'")
        elif self.LLM_PROVIDER.lower() == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is set to 'openai'")

        if self.EMBEDDING_TYPE.lower() == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_TYPE is set to 'gemini'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__class__.model_fields:
            super().__setattr__(name, value)
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name in self.__class__.model_fields:
            super().__delattr__(name)
        else:
            object.__delattr__(self, name)


settings = Settings()
