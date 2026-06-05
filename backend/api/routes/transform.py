"""
NeuraCore Transform Router — AI-Powered Transformation (Phase 2)
=================================================================
POST /api/transform
    Rewrite a single curriculum atom for a cognitive profile.

POST /api/transform/batch
    Rewrite multiple atoms for a single profile in one call.

Single request body:
    {
        "atom_id": "atom_001",
        "text":    "Raw curriculum text…",
        "profile": "adhd"          // "adhd" | "dyslexia" | "asd"
    }

Single response:
    {
        "atom_id":        "atom_001",
        "profile":        "adhd",
        "original_text":  "…",
        "rewritten_text": "🎯 MISSION: …"
    }
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.transformers import transform_atom
from core.models import TransformRequestSchema, TransformResponseSchema

router = APIRouter(prefix="/api", tags=["transformation"])

_VALID_PROFILES = {"adhd", "dyslexia", "asd"}


# ---------------------------------------------------------------------------
# Pydantic models for batch operations
# ---------------------------------------------------------------------------

class BatchTransformRequest(BaseModel):
    """Request to transform multiple atoms at once."""
    atoms: list[dict]  # [{id, text}, …]
    profile: str

    class Config:
        json_schema_extra = {
            "example": {
                "atoms": [
                    {"id": "atom_001", "text": "The mitochondria..."},
                    {"id": "atom_002", "text": "Photosynthesis is..."},
                ],
                "profile": "adhd",
            }
        }


class BatchTransformResponse(BaseModel):
    """Response containing multiple transformed atoms."""
    results: list[TransformResponseSchema]
    count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/transform", response_model=TransformResponseSchema)
async def transform_endpoint(body: TransformRequestSchema):
    """Rewrite a single curriculum atom for the given cognitive profile."""
    try:
        rewritten = await transform_atom(body.text, body.profile)  # type: ignore[arg-type]
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI transformation failed: {exc}. Check your API key and model name.",
        )

    return TransformResponseSchema(
        atom_id=body.atom_id,
        profile=body.profile,
        original_text=body.text,
        rewritten_text=rewritten,
    )


@router.post("/transform/batch", response_model=BatchTransformResponse)
async def transform_batch(body: BatchTransformRequest):
    """
    Transform multiple atoms for one profile in a single call.
    Runs sequentially to respect rate limits.
    """
    results = []
    for atom in body.atoms:
        atom_id = atom.get("id", "unknown")
        text = atom.get("text", "").strip()
        if not text:
            continue
        try:
            rewritten = await transform_atom(text, body.profile)  # type: ignore[arg-type]
            results.append(
                TransformResponseSchema(
                    atom_id=atom_id,
                    profile=body.profile,
                    original_text=text,
                    rewritten_text=rewritten,
                )
            )
        except Exception as exc:
            results.append(
                TransformResponseSchema(
                    atom_id=atom_id,
                    profile=body.profile,
                    original_text=text,
                    rewritten_text=f"[Transform failed: {exc}]",
                )
            )

    return BatchTransformResponse(results=results, count=len(results))
