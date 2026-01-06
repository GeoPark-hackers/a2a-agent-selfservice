"""Configuration management for the A2A Self-Service platform."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Azure Configuration
    azure_subscription_id: str = Field(default="")
    azure_resource_group: str = Field(default="")
    azure_keyvault_name: str = Field(default="")
    azure_client_id: str = Field(default="")
    azure_tenant_id: str = Field(default="")

    # LLM Configuration
    llm_provider: Literal["azure_openai", "google_ai"] = Field(default="azure_openai")
    azure_openai_endpoint: str = Field(default="")
    azure_openai_api_key: str = Field(default="")
    azure_openai_deployment_name: str = Field(default="gpt-4o")
    azure_openai_api_version: str = Field(default="2024-08-01-preview")
    google_api_key: str = Field(default="")

    # Application Configuration
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    app_debug: bool = Field(default=False)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Cosmos DB Configuration
    cosmos_connection_string: str = Field(default="")

    # A2A Configuration
    a2a_service_url: str = Field(default="http://localhost:8000")
    a2a_service_name: str = Field(default="a2a-agent-selfservice")


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
