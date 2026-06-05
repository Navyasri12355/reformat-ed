"""SQLAlchemy ORM models — the relational core of NeuraCore.

Mirrors the schema in the implementation plan, adapted to be portable across
SQLite (local/dev) and PostgreSQL (production). UUID primary keys are stored as
32-char hex strings so they behave identically on both backends.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    lms_type: Mapped[str] = mapped_column(String(32), default="none")
    lti_client_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    auto_approve_transforms: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    users: Mapped[list["User"]] = relationship(back_populates="institution")

    __table_args__ = (
        CheckConstraint(
            "lms_type IN ('canvas','google_classroom','msteams','none')",
            name="ck_institution_lms_type",
        ),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    institution_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("institutions.id"), nullable=True
    )
    # COPPA: students under 13 require recorded parental consent before profiling.
    parental_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped[Institution | None] = relationship(back_populates="users")
    profile: Mapped["CognitiveProfile | None"] = relationship(
        back_populates="student", uselist=False
    )

    __table_args__ = (
        CheckConstraint("role IN ('educator','student','admin')", name="ck_user_role"),
    )


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    uploaded_by: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    institution_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("institutions.id"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(8), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    atoms: Mapped[list["CurriculumAtom"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    institution: Mapped[Institution | None] = relationship()

    __table_args__ = (
        CheckConstraint("file_type IN ('pdf','docx','pptx','txt')", name="ck_doc_file_type"),
        CheckConstraint(
            "parse_status IN ('pending','processing','complete','failed')",
            name="ck_doc_parse_status",
        ),
    )


class CurriculumAtom(Base):
    __tablename__ = "curriculum_atoms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False
    )
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    bloom_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    estimated_reading_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    document: Mapped[SourceDocument] = relationship(back_populates="atoms")

    __table_args__ = (
        UniqueConstraint("document_id", "sequence_index", name="uq_atom_doc_seq"),
        CheckConstraint(
            "bloom_level IN ('remember','understand','apply','analyse','evaluate','create')",
            name="ck_atom_bloom",
        ),
    )


class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), unique=True, nullable=False
    )
    adhd_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    dyslexia_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    asd_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    calibration_source: Mapped[str] = mapped_column(String(16), default="onboarding", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    student: Mapped[User] = relationship(back_populates="profile")
    snapshots: Mapped[list["CognitiveProfileSnapshot"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "calibration_source IN ('onboarding','educator','auto')",
            name="ck_profile_calibration_source",
        ),
    )


class CognitiveProfileSnapshot(Base):
    """Immutable, append-only history of profile states."""

    __tablename__ = "cognitive_profile_snapshots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("cognitive_profiles.id"), nullable=False
    )
    adhd_weight: Mapped[float] = mapped_column(Float, nullable=False)
    dyslexia_weight: Mapped[float] = mapped_column(Float, nullable=False)
    asd_weight: Mapped[float] = mapped_column(Float, nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    profile: Mapped[CognitiveProfile] = relationship(back_populates="snapshots")


class TransformedAtom(Base):
    __tablename__ = "transformed_atoms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    atom_id: Mapped[str] = mapped_column(String(32), ForeignKey("curriculum_atoms.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    # Profile state captured at generation time (snapshot, not a live FK).
    adhd_weight: Mapped[float] = mapped_column(Float, nullable=False)
    dyslexia_weight: Mapped[float] = mapped_column(Float, nullable=False)
    asd_weight: Mapped[float] = mapped_column(Float, nullable=False)
    output_format: Mapped[str] = mapped_column(String(24), nullable=False)
    transformed_text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_script: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured per-format scaffolding (goal, anchor, poll, schedule, idioms,
    # rubric, keywords, real_world). See services/enrich.py.
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(32), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(16), nullable=False)
    generation_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    atom: Mapped[CurriculumAtom] = relationship()

    __table_args__ = (
        CheckConstraint(
            "output_format IN ('adhd_gamified','dyslexia_audio','asd_structured','blended')",
            name="ck_transform_format",
        ),
        CheckConstraint(
            "review_status IN ('pending','approved','rejected','auto_approved')",
            name="ck_transform_review",
        ),
    )


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(32), ForeignKey("source_documents.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_atoms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    atoms_completed: Mapped[int] = mapped_column(Integer, default=0)


class SessionEvent(Base):
    """Append-only passive behavioural signals. Never updated or deleted in flight."""

    __tablename__ = "session_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("learning_sessions.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    atom_id: Mapped[str] = mapped_column(String(32), ForeignKey("curriculum_atoms.id"), nullable=False)
    transformed_atom_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("transformed_atoms.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(24), nullable=False)
    time_on_atom_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('atom_start','atom_complete','atom_skip','atom_retry',"
            "'audio_play','audio_pause','font_size_change','exit_mid_atom')",
            name="ck_event_type",
        ),
    )
