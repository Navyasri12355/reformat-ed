import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import session_scope
from app.models import SourceDocument, TransformedAtom, CurriculumAtom

with session_scope() as db:
    doc = db.query(SourceDocument).filter(SourceDocument.file_name == 'Unit - 3_DCN_3-6-2025.pdf').first()
    target_student_id = '72c45f3462e64c95848689ff487eb61e'
    rows = (
        db.query(TransformedAtom)
        .join(CurriculumAtom, CurriculumAtom.id == TransformedAtom.atom_id)
        .filter(
            CurriculumAtom.document_id == doc.id,
            TransformedAtom.student_id == target_student_id,
            TransformedAtom.output_format == 'dyslexia_audio',
        )
        .all()
    )
    print('count', len(rows))
    for i, ta in enumerate(rows[:5], start=1):
        print(i, ta.id, 'meta keys', list(ta.meta.keys()) if ta.meta else None)
        print('  simulator present?', 'simulator' in (ta.meta or {}))
        print('  keywords', ta.meta.get('keywords') if ta.meta else None)
        print('  diagram present?', 'diagram' in (ta.meta or {}))
        print('  transformed_text first line', ta.transformed_text.splitlines()[0])
        print('  raw_text first line', ta.atom.raw_text.splitlines()[0])
        print('---')
