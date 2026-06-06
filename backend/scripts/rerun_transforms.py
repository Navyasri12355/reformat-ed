import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import session_scope
from app.models import SourceDocument, CognitiveProfile
from app.tasks import transform_document_for_student

with session_scope() as db:
    doc = db.query(SourceDocument).order_by(SourceDocument.created_at.desc()).first()
    if doc is None:
        raise SystemExit('No SourceDocument found')
    profile = db.query(CognitiveProfile).order_by(CognitiveProfile.created_at.desc()).first()
    if profile is None:
        raise SystemExit('No CognitiveProfile found')
    print('Rerunning transforms for document:', doc.id, 'file:', doc.file_name)
    print('Student id:', profile.student_id)
    result = transform_document_for_student(doc.id, profile.student_id, force_auto_approve=True)
    print('Result:', result)
