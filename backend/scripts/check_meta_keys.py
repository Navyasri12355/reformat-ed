import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import session_scope
from sqlalchemy import select
from app.models import SourceDocument, TransformedAtom, CurriculumAtom

with session_scope() as db:
    doc = db.query(SourceDocument).filter(SourceDocument.file_name == 'Unit - 3_DCN_3-6-2025.pdf').first()
    if not doc:
        print('Doc not found')
        raise SystemExit(1)
    target_student_id = '72c45f3462e64c95848689ff487eb61e'
    rows = db.query(TransformedAtom).join(CurriculumAtom, CurriculumAtom.id == TransformedAtom.atom_id).filter(CurriculumAtom.document_id == doc.id, TransformedAtom.student_id == target_student_id).order_by(CurriculumAtom.sequence_index).all()
    print('count', len(rows))
    for i, ta in enumerate(rows[:10], start=1):
        print(i, ta.id, ta.output_format, 'meta keys', list(ta.meta.keys()) if ta.meta else None)
        print('  simulator present?', 'simulator' in (ta.meta or {}))
        print('  diagram present?', 'diagram' in (ta.meta or {}))
        print('  keywords', ta.meta.get('keywords') if ta.meta else None)
        if i >= 10:
            break
