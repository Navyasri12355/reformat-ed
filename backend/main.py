"""
NeuraCore API — Unified entry point
====================================
Consolidates Phase 1 (document ingestion) and Phase 2 (AI transformation).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.routes import upload_router, transform_router

# Validate configuration
try:
    settings.validate()
except RuntimeError as e:
    print(f"⚠️  Warning: {e}")

app = FastAPI(
    title="NeuraCore API",
    description="Adaptive Learning Platform for Neurodivergent Students",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload_router)
app.include_router(transform_router)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "NeuraCore API is running 🧠",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/upload — upload curriculum files",
            "transform": "POST /api/transform — transform atoms for profiles",
            "batch_transform": "POST /api/transform/batch — batch transform",
            "docs": "GET /docs — interactive API documentation",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
