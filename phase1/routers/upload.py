from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from document_parser import parse_document

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accept a curriculum file (PDF, DOCX, or TXT) and return
    a list of curriculum atoms ready for transformation.

    Response shape:
    {
        "filename": "lesson.pdf",
        "atom_count": 7,
        "atoms": [
            {"id": "atom_001", "text": "...", "word_count": 142},
            ...
        ]
    }
    """
    # Validate file is present
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Read bytes (FastAPI streams — read fully for parsing)
    try:
        data = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Size guard — 10 MB should cover any hackathon demo file
    MAX_BYTES = 10 * 1024 * 1024
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data) // 1024} KB). Max is 10 MB.",
        )

    # Parse
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

    return JSONResponse(
        content={
            "filename": file.filename,
            "atom_count": len(atoms),
            "atoms": atoms,
        }
    )