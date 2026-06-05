"""
NeuraCore Upload Router — Document Ingestion (Phase 1)
=======================================================
POST /api/upload
  Accepts a curriculum file (PDF, DOCX, TXT) and returns clean curriculum atoms.

Response shape:
    {
        "filename":   "lesson.pdf",
        "atom_count": 7,
        "atoms": [
            {"id": "atom_001", "text": "…", "word_count": 142},
            …
        ]
    }
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from core.parsers import parse_document
from core.models import UploadResponseSchema

router = APIRouter(prefix="/api", tags=["ingestion"])

MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=UploadResponseSchema)
async def upload_document(file: UploadFile = File(...)):
    """Upload a curriculum file and receive a list of curriculum atoms."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    try:
        data = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data) // 1024} KB). Max is 10 MB.",
        )

    try:
        atoms = parse_document(data, file.filename, file.content_type or "")
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {exc}. Try a simpler file or plain text.",
        )

    if not atoms:
        raise HTTPException(
            status_code=422,
            detail="No readable text could be extracted from this file.",
        )

    return UploadResponseSchema(
        filename=file.filename,
        atom_count=len(atoms),
        atoms=[
            {
                "id": atom["id"],
                "text": atom["text"],
                "word_count": atom["word_count"],
            }
            for atom in atoms
        ],
    )
