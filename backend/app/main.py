"""FastAPI application factory for NeuraCore."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import init_db
from app.logging_config import configure_logging
from app.routers import analytics, auth, documents, profiles, sessions, transforms, tts


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=__version__,
        description="Adaptive learning platform for neurodivergent students.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(profiles.router)
    app.include_router(transforms.router)
    app.include_router(sessions.router)
    app.include_router(analytics.router)
    app.include_router(tts.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        llm_active = bool(settings.openai_api_key)
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": __version__,
            "task_backend": settings.task_backend,
            "llm": "active" if llm_active else "local-rules",
            "llm_model": settings.openai_model if llm_active else None,
            "llm_endpoint": settings.openai_base_url if llm_active else None,
        }

    return app


app = create_app()
