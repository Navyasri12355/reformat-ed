"""
NeuraCore — Settings
=====================
All configuration loaded from environment variables / .env file.

Usage:
    from core.config import settings
"""
import os
from dotenv import load_dotenv

# Load .env from the backend/ directory (where this file lives)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


class Settings:
    OPENAI_API_KEY:    str       = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str       = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL:             str       = os.getenv("MODEL", "gpt-4o")
    CORS_ORIGINS:      list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    def validate(self) -> None:
        if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "No AI API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in backend/.env"
            )


settings = Settings()
