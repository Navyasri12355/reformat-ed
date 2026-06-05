"""Document upload, listing and parse-status polling."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_educator
from app.config import settings
from app.database import get_db
from app.models import CurriculumAtom, SourceDocument, User
from app.schemas import (
    AtomOut,
    DocumentOut,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.services import parsers, storage
from app.tasks import run_ingestion

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    subject: str | None = Form(None),
    grade_level: str | None = Form(None),
    educator: User = Depends(require_educator),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    file_type = parsers.detect_file_type(file.filename or "")
    if file_type is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type. Allowed: {', '.join(parsers.SUPPORTED_TYPES)}",
        )

    data = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds {settings.max_file_size_mb} MB limit",
        )

    key = storage.build_key(file.filename or f"upload.{file_type}")
    storage.put(key, data)

    doc = SourceDocument(
        uploaded_by=educator.id,
        institution_id=educator.institution_id,
        file_name=file.filename or f"upload.{file_type}",
        file_type=file_type,
        storage_key=key,
        file_size_bytes=len(data),
        subject_override=subject,
        grade_override=grade_level,
        parse_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    task_id = run_ingestion(doc.id)
    return DocumentUploadResponse(
        document_id=doc.id,
        task_id=task_id,
        status="processing",
        poll_url=f"/documents/{doc.id}/status",
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SourceDocument]:
    stmt = select(SourceDocument).order_by(SourceDocument.created_at.desc())
    if user.role == "educator":
        stmt = stmt.where(SourceDocument.uploaded_by == user.id)
    elif user.role != "admin" and user.institution_id:
        stmt = stmt.where(SourceDocument.institution_id == user.institution_id)
    return list(db.scalars(stmt).all())


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def document_status(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentStatusResponse:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    atom_count = db.scalar(
        select(func.count()).select_from(CurriculumAtom).where(
            CurriculumAtom.document_id == document_id
        )
    ) or 0
    # ~5s of model + overhead per atom, expressed in minutes.
    estimate = round(atom_count * 5 / 60, 1)
    return DocumentStatusResponse(
        document_id=doc.id,
        parse_status=doc.parse_status,
        parse_error=doc.parse_error,
        atom_count=atom_count,
        estimated_transform_minutes=estimate,
    )


@router.get("/{document_id}/atoms", response_model=list[AtomOut])
def list_atoms(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CurriculumAtom]:
    if db.get(SourceDocument, document_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return list(
        db.scalars(
            select(CurriculumAtom)
            .where(CurriculumAtom.document_id == document_id)
            .order_by(CurriculumAtom.sequence_index)
        ).all()
    )
