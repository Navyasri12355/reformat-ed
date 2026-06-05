"""Pydantic request/response schemas (API contracts)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["educator", "student", "admin"]
QuizAnswer = Literal["never", "sometimes", "often", "always"]
OutputFormat = Literal["adhd_gamified", "dyslexia_audio", "asd_structured", "blended"]
ReviewStatus = Literal["pending", "approved", "rejected", "auto_approved"]


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    display_name: str
    role: Role = "student"
    institution_id: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    role: Role
    institution_id: str | None = None


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    file_name: str
    file_type: str
    parse_status: str
    page_count: int | None = None
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    task_id: str
    status: str
    poll_url: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    parse_status: str
    parse_error: str | None = None
    atom_count: int
    estimated_transform_minutes: float


class AtomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    sequence_index: int
    raw_text: str
    subject: str | None = None
    grade_level: str | None = None
    bloom_level: str | None = None
    estimated_reading_minutes: float | None = None


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
class ProfileWeightsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    adhd_weight: float
    dyslexia_weight: float
    asd_weight: float
    profile_version: int
    calibration_source: str
    last_calibrated_at: datetime


class ProfileUpdateRequest(BaseModel):
    adhd_weight: float = Field(ge=0.0, le=1.0)
    dyslexia_weight: float = Field(ge=0.0, le=1.0)
    asd_weight: float = Field(ge=0.0, le=1.0)
    calibration_source: Literal["educator", "onboarding"] = "educator"
    snapshot_reason: str | None = None


class QuizQuestionOut(BaseModel):
    id: str
    text: str


class QuizSubmission(BaseModel):
    answers: dict[str, QuizAnswer]


class ProfileSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    adhd_weight: float
    dyslexia_weight: float
    asd_weight: float
    profile_version: int
    snapshot_reason: str | None = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Transforms
# --------------------------------------------------------------------------- #
class TransformRequest(BaseModel):
    document_id: str
    student_id: str | None = None  # educators may target a student; students implicit


class TransformBatchResponse(BaseModel):
    transform_batch_id: str
    document_id: str
    student_id: str
    atom_count: int
    task_ids: list[str]
    review_required: bool


class TransformedAtomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    atom_id: str
    sequence_index: int | None = None
    output_format: OutputFormat
    transformed_text: str
    audio_script: str | None = None
    meta: dict[str, Any] | None = None
    review_status: ReviewStatus


class StudentContentResponse(BaseModel):
    document_id: str
    student_id: str
    profile_snapshot: dict[str, float]
    atoms: list[TransformedAtomOut]


class ReviewQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transformed_atom_id: str
    atom_id: str
    output_format: OutputFormat
    review_status: ReviewStatus
    atom_preview: str
    transform_preview: str
    file_name: str
    created_at: datetime


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int
    page: int


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject"]
    edited_text: str | None = None
    rejection_note: str | None = None


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
class SessionStartRequest(BaseModel):
    document_id: str


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    started_at: datetime
    ended_at: datetime | None = None
    total_atoms: int | None = None
    atoms_completed: int


class SessionEventRequest(BaseModel):
    atom_id: str
    transformed_atom_id: str | None = None
    event_type: Literal[
        "atom_start",
        "atom_complete",
        "atom_skip",
        "atom_retry",
        "audio_play",
        "audio_pause",
        "font_size_change",
        "exit_mid_atom",
    ]
    time_on_atom_ms: int | None = None
    retry_count: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
class AtomAnalyticsRow(BaseModel):
    student_id: str
    student_name: str
    atom_id: str
    sequence_index: int
    output_format: str | None = None
    completions: int
    retries: int
    exits: int
    avg_time_ms: float | None = None


# --------------------------------------------------------------------------- #
# Support & Feedback
# --------------------------------------------------------------------------- #
class SupportRequest(BaseModel):
    question: str | None = None


class SupportResponse(BaseModel):
    response: str


class FeedbackCreate(BaseModel):
    message: str


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_name: str
    sequence_index: int
    message: str
    created_at: datetime
