import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import session_scope
from app.models import SourceDocument, TransformedAtom
import json

with session_scope() as db:
    ta = db.query(TransformedAtom).order_by(TransformedAtom.created_at.desc()).first()
    if not ta:
        print('No transformed atom')
        raise SystemExit(1)
    print('TransformedAtom id:', ta.id)
    print('output_format:', ta.output_format)
    print('created_at:', ta.created_at)
    print('\ntransformed_text:\n', ta.transformed_text)
    if ta.atom is not None:
        print('\nraw_text:\n', ta.atom.raw_text)
    else:
        print('\nraw_text: NO RELATIONSHIP LOADED')
    print('\nmeta keywords:', ta.meta.get('keywords') if ta.meta else None)
    print('\nmeta simulator:', json.dumps(ta.meta.get('simulator') if ta.meta else None, indent=2)[:2000])
