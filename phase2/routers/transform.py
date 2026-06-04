"""
Phase 2 — /api/transform router
=================================
Accepts a curriculum atom + cognitive profile and returns an AI-rewritten version.

POST /api/transform
  Body (JSON):
    {
      "atom_id":  "atom_001",          // from Phase 1 /upload response
      "text":     "Raw curriculum text…",
      "profile":  "adhd"               // "adhd" | "dyslexia" | "asd"
    }

  Response:
    {
      "atom_id":       "atom_001",
      "profile":       "adhd",
      "original_text": "Raw curriculum text…",
      "rewritten_text": "🎯 MISSION: …"
    }
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from transformer import transform_atom

router = APIRouter(prefix="/api", tags=["transformation"])


# ── Request / Response models ──────────────────────────────────────────────

class TransformRequest(BaseModel):
    atom_id:  str
    text:     str
    profile:  str          # validated below

    @field_validator("profile")
    @classmethod
    def profile_must_be_valid(cls, v: str) -> str:
        valid = {"adhd", "dyslexia", "asd"}
        v = v.lower().strip()
        if v not in valid:
            raise ValueError(f"profile must be one of {valid}, got '{v}'")
        return v

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v.strip()


class TransformResponse(BaseModel):
    atom_id:       str
    profile:       str
    original_text: str
    rewritten_text: str


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/transform", response_model=TransformResponse)
async def transform_endpoint(body: TransformRequest):
    """
    Rewrite a curriculum atom for the given cognitive profile.
    """
    try:
        rewritten = await transform_atom(body.text, body.profile)  # type: ignore[arg-type]
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI transformation failed: {exc}. Check your API key and model name."
        )

    return TransformResponse(
        atom_id=body.atom_id,
        profile=body.profile,
        original_text=body.text,
        rewritten_text=rewritten,
    )


# ── Batch endpoint (optional but useful for the hackathon) ─────────────────

class BatchTransformRequest(BaseModel):
    atoms:   list[dict]   # list of {id, text}
    profile: str

    @field_validator("profile")
    @classmethod
    def profile_must_be_valid(cls, v: str) -> str:
        valid = {"adhd", "dyslexia", "asd"}
        v = v.lower().strip()
        if v not in valid:
            raise ValueError(f"profile must be one of {valid}, got '{v}'")
        return v


@router.post("/transform/batch")
async def transform_batch(body: BatchTransformRequest):
    """
    Transform multiple atoms in one call (sequential to respect rate limits).
    Returns a list of TransformResponse objects.
    """
    results = []
    for atom in body.atoms:
        atom_id = atom.get("id", "unknown")
        text    = atom.get("text", "").strip()
        if not text:
            continue
        try:
            rewritten = await transform_atom(text, body.profile)  # type: ignore[arg-type]
            results.append({
                "atom_id":       atom_id,
                "profile":       body.profile,
                "original_text": text,
                "rewritten_text": rewritten,
            })
        except Exception as exc:
            results.append({
                "atom_id":       atom_id,
                "profile":       body.profile,
                "original_text": text,
                "rewritten_text": f"[Transform failed: {exc}]",
                "error":         True,
            })
    return {"results": results, "count": len(results)}
