import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import session_scope
from app.models import TransformedAtom

with session_scope() as db:
    ta = db.query(TransformedAtom).order_by(TransformedAtom.created_at.desc()).first()
    print('meta repr:', repr(ta.meta))
    print('meta type:', type(ta.meta))
    print('meta keys:', list(ta.meta.keys()))
    for key, value in ta.meta.items():
        print('key:', key, 'type:', type(value), 'value repr:', repr(value)[:500])
