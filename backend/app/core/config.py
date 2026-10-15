from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "lumen-forge-ryan-vo"
    version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # LLM (optional)
    llm_api_key: str | None = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str | None = None

    # Auth (Keycloak)
    oidc_issuer_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None


settings = Settings()