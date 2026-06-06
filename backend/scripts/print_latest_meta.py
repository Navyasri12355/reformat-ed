import sys, os
# Ensure project root is on sys.path so 'app' imports work when run as script
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import session_scope
from app.models import TransformedAtom
import json

with session_scope() as db:
    rows = db.query(TransformedAtom).order_by(TransformedAtom.created_at.desc()).limit(5).all()
    if not rows:
        print('No transformed atoms found')
    for r in rows:
        print('---')
        print('id:', r.id)
        print('created_at:', r.created_at)
        print('output_format:', r.output_format)
        print('\ntransformed_text:\n', r.transformed_text[:2000])
        print('\nmeta:\n', json.dumps(r.meta, indent=2)[:4000])
        print('\nfull meta length:', len(json.dumps(r.meta)))
        break
