"""
Pydantic schemas for NeuraCore API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class AtomSchema(BaseModel):
    """A curriculum atom — a single logical chunk of content."""
    id: str = Field(..., description="Unique atom identifier")
    text: str = Field(..., description="Curriculum text")
    word_count: int = Field(..., description="Number of words in atom")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "atom_001",
                "text": "The mitochondria is the powerhouse of the cell...",
                "word_count": 42,
            }
        }


class UploadResponseSchema(BaseModel):
    """Response from /api/upload endpoint."""
    filename: str = Field(..., description="Uploaded file name")
    atom_count: int = Field(..., description="Total number of atoms extracted")
    atoms: list[AtomSchema] = Field(..., description="List of curriculum atoms")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "lesson.pdf",
                "atom_count": 3,
                "atoms": [
                    {
                        "id": "atom_001",
                        "text": "Sample curriculum text...",
                        "word_count": 120,
                    },
                ],
            }
        }


class CognitiveProfile(BaseModel):
    """Student cognitive profile weights."""
    adhd: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="ADHD trait weight (0.0-1.0)"
    )
    dyslexia: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Dyslexia trait weight (0.0-1.0)"
    )
    asd: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Autism spectrum trait weight (0.0-1.0)"
    )

    def get_dominant_profile(self) -> str:
        """Return the profile with the highest weight."""
        profiles = {"adhd": self.adhd, "dyslexia": self.dyslexia, "asd": self.asd}
        return max(profiles, key=profiles.get)


class TransformRequestSchema(BaseModel):
    """Request body for /api/transform endpoint."""
    atom_id: str = Field(..., description="ID of the atom to transform")
    text: str = Field(..., description="Atom text to transform")
    profile: Literal["adhd", "dyslexia", "asd"] = Field(
        ...,
        description="Target cognitive profile"
    )

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v):
        if v not in ("adhd", "dyslexia", "asd"):
            raise ValueError(
                f"Invalid profile '{v}'. Must be one of: 'adhd', 'dyslexia', 'asd'"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "atom_id": "atom_001",
                "text": "The mitochondria is the powerhouse of the cell...",
                "profile": "adhd",
            }
        }


class TransformResponseSchema(BaseModel):
    """Response from /api/transform endpoint."""
    atom_id: str = Field(..., description="ID of the transformed atom")
    profile: str = Field(..., description="Cognitive profile used")
    original_text: str = Field(..., description="Original atom text")
    rewritten_text: str = Field(..., description="AI-rewritten text")

    class Config:
        json_schema_extra = {
            "example": {
                "atom_id": "atom_001",
                "profile": "adhd",
                "original_text": "The mitochondria is...",
                "rewritten_text": "🎯 MISSION: DISCOVER CELLULAR POWER...",
            }
        }
