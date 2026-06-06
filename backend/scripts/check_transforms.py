import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import session_scope
from app.models import SourceDocument, TransformedAtom

with session_scope() as db:
    doc = db.query(SourceDocument).order_by(SourceDocument.created_at.desc()).first()
    if doc is None:
        print('No SourceDocument found')
        raise SystemExit(1)
    count = db.query(TransformedAtom).filter(TransformedAtom.atom.has(document_id=doc.id)).count()
    print('Document:', doc.id, 'file:', doc.file_name)
    print('Transformed atom count:', count)
    last = db.query(TransformedAtom).filter(TransformedAtom.atom.has(document_id=doc.id)).order_by(TransformedAtom.created_at.desc()).first()
    if last:
        print('Last transformed atom created_at:', last.created_at)
    else:
        print('No transformed atoms for this document')
