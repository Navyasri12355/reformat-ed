"""
NeuraCore API — Phase 2 main entry point
=========================================
Extends the Phase 1 upload/ingestion functionality with the Phase 2
cognitive-profile transformation endpoints.

Run:
    cd phase2
    uvicorn main:app --reload --port 8000
"""

import sys, os

# Pull in Phase 1 modules (document_parser, config, routers/upload)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "phase1"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload           # Phase 1
from routers.transform import router as transform_router  # Phase 2

app = FastAPI(
    title="NeuraCore API",
    description="Adaptive Learning for Neurodivergent Students — Phase 1 + 2",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1: document ingestion
app.include_router(upload.router)

# Phase 2: cognitive-profile transformation
app.include_router(transform_router)


@app.get("/")
def health_check():
    return {
        "status":  "ok",
        "message": "NeuraCore API v0.2 — Phase 1 (ingest) + Phase 2 (transform) live 🧠",
        "endpoints": [
            "POST /api/upload   — upload PDF/DOCX/TXT → curriculum atoms",
            "POST /api/transform — atom + profile → AI-rewritten content",
            "POST /api/transform/batch — multiple atoms at once",
        ],
    }
