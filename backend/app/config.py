"""Application configuration, driven entirely by environment variables.

Every setting has a sensible default so the stack boots with zero configuration
for local development and demos. Provide a ``.env`` file (see ``.env.example``)
to override anything for staging / production.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "NeuraCore"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Database ---
    # Defaults to a local SQLite file so it runs with no external services.
    # For Postgres: postgresql+psycopg://user:pass@host:5432/neuracore
    database_url: str = f"sqlite:///{(BACKEND_ROOT / 'neuracore.db').as_posix()}"

    # --- Storage ---
    # Local filesystem store for uploaded documents (no S3 needed for dev).
    storage_dir: str = (BACKEND_ROOT / "storage").as_posix()

    # --- Auth ---
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # --- AI transformation ---
    # If openai_api_key is empty, the engine uses a deterministic local
    # rule-based transformer so the whole product works offline.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-2024-11-20"
    openai_timeout_seconds: int = 45
    openai_temperature: float = 0.4

    # --- Prompts ---
    active_prompt_version: str = "1.0.0"
    prompts_dir: str = (BACKEND_ROOT / "prompts").as_posix()

    # --- Text-to-speech (Coqui) ---
    # If the `TTS` package is installed, audio is synthesised server-side with
    # this model; otherwise the frontend uses the browser voice with the same
    # per-profile modulation. `pip install TTS` to enable Coqui.
    coqui_model: str = "tts_models/en/ljspeech/tacotron2-DDC"

    # --- Task execution ---
    # "inline" runs ingestion/transform synchronously in a background thread
    # (no Redis/Celery required). "celery" dispatches to Celery workers.
    task_backend: str = "inline"
    redis_url: str = "redis://localhost:6379/0"

    # --- Review ---
    # When true, transformed atoms skip the educator review queue (handy for a
    # single-user demo so a student can prepare and immediately learn).
    auto_approve_all: bool = False

    # --- Limits ---
    max_file_size_mb: int = 50
    max_atoms_per_document: int = 500

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_minutes * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 3600


settings = Settings()
