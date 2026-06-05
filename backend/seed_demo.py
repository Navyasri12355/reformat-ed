"""Seed a demo institution, educator and student with known credentials.

Run once after starting the backend (or before):

    python seed_demo.py

Then log in via the frontend with the printed credentials.
"""

from __future__ import annotations

from sqlalchemy import select

from app.auth import hash_password
from app.database import init_db, session_scope
from app.models import CognitiveProfile, Institution, User

DEMO_EDUCATOR = ("teacher@neuracore.demo", "password123", "Ms. Rivera")
DEMO_STUDENT = ("student@neuracore.demo", "password123", "Alex")


def _get_or_create_user(db, email, password, name, role, institution_id):
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            display_name=name,
            role=role,
            password_hash=hash_password(password),
            institution_id=institution_id,
        )
        db.add(user)
        db.flush()
    return user


def main() -> None:
    init_db()
    with session_scope() as db:
        inst = db.scalar(select(Institution).where(Institution.name == "NeuraCore Demo School"))
        if inst is None:
            inst = Institution(name="NeuraCore Demo School", lms_type="none")
            db.add(inst)
            db.flush()

        _get_or_create_user(db, *DEMO_EDUCATOR, role="educator", institution_id=inst.id)
        student = _get_or_create_user(db, *DEMO_STUDENT, role="student", institution_id=inst.id)

        if db.scalar(select(CognitiveProfile).where(CognitiveProfile.student_id == student.id)) is None:
            # A dyslexia-leaning starter profile so the demo shows audio-first content.
            db.add(
                CognitiveProfile(
                    student_id=student.id,
                    adhd_weight=0.2,
                    dyslexia_weight=0.7,
                    asd_weight=0.1,
                    calibration_source="onboarding",
                )
            )

    print("Demo data ready.\n")
    print(f"  Educator:  {DEMO_EDUCATOR[0]}  /  {DEMO_EDUCATOR[1]}")
    print(f"  Student:   {DEMO_STUDENT[0]}  /  {DEMO_STUDENT[1]}")


if __name__ == "__main__":
    main()
