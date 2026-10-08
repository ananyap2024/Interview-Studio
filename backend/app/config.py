from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Mock Interview API"
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    supabase_db_url: str | None = None
    gemini_api_key: str | None = None
    llm_model: str = "gemini-3.5-flash-lite"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


settings = Settings()