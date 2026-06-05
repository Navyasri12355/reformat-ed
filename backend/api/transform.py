"""
NeuraCore — Transform Router  (Phase 2)
=========================================
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
from pydantic import BaseModel, field_validator

from core.transformer import transform_atom

router = APIRouter(prefix="/api", tags=["transformation"])

_VALID_PROFILES = {"adhd", "dyslexia", "asd"}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TransformRequest(BaseModel):
    atom_id: str
    text:    str
    profile: str

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in _VALID_PROFILES:
            raise ValueError(f"profile must be one of {_VALID_PROFILES}, got '{v}'")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v.strip()


class TransformResponse(BaseModel):
    atom_id:        str
    profile:        str
    original_text:  str
    rewritten_text: str


class BatchTransformRequest(BaseModel):
    atoms:   list[dict]   # [{id, text}, …]
    profile: str

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in _VALID_PROFILES:
            raise ValueError(f"profile must be one of {_VALID_PROFILES}, got '{v}'")
        return v


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/transform", response_model=TransformResponse)
async def transform_endpoint(body: TransformRequest):
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

    return TransformResponse(
        atom_id=body.atom_id,
        profile=body.profile,
        original_text=body.text,
        rewritten_text=rewritten,
    )


@router.post("/transform/batch")
async def transform_batch(body: BatchTransformRequest):
    """
    Transform multiple atoms for one profile in a single call.
    Runs sequentially to respect rate limits.
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
                "atom_id":        atom_id,
                "profile":        body.profile,
                "original_text":  text,
                "rewritten_text": rewritten,
            })
        except Exception as exc:
            results.append({
                "atom_id":        atom_id,
                "profile":        body.profile,
                "original_text":  text,
                "rewritten_text": f"[Transform failed: {exc}]",
                "error":          True,
            })

    return {"results": results, "count": len(results)}
