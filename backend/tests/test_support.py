from sqlalchemy import select
from app.database import SessionLocal
from app.models import CognitiveProfile, CurriculumAtom, TransformedAtom, User, StudentFeedback
from app.services.sync import sync_student_transforms
from app.services.prompt_router import ProfileWeights, select_output_format
from app.auth import create_access_token


def test_sync_student_transforms_deletes_outdated_formats():
    with SessionLocal() as db:
        # Setup a student
        student = User(email="test_sync@demo.com", display_name="Test Sync Student", role="student")
        db.add(student)
        db.commit()

        # Create a profile
        profile = CognitiveProfile(student_id=student.id, adhd_weight=0.9, dyslexia_weight=0.0, asd_weight=0.0)
        db.add(profile)
        db.commit()

        # Verify select_output_format is adhd_gamified
        weights = ProfileWeights(adhd=0.9, dyslexia=0.0, asd=0.0)
        assert select_output_format(weights) == "adhd_gamified"

        # Create document and atoms
        from app.models import SourceDocument
        doc = SourceDocument(uploaded_by=student.id, file_name="test.txt", file_type="txt", storage_key="test_key")
        db.add(doc)
        db.commit()

        atom = CurriculumAtom(document_id=doc.id, sequence_index=1, raw_text="Original text content.")
        db.add(atom)
        db.commit()

        # Add TransformedAtom in asd_structured format (outdated!)
        ta = TransformedAtom(
            atom_id=atom.id,
            student_id=student.id,
            adhd_weight=0.0,
            dyslexia_weight=0.0,
            asd_weight=0.9,
            output_format="asd_structured",
            transformed_text="Structured text content.",
            audio_script="Structured text content.",
            llm_model="test_model",
            prompt_version="1.0.0",
            review_status="approved",
        )
        db.add(ta)
        db.commit()

        # Run sync: this should identify that "asd_structured" is outdated (since weights say "adhd_gamified")
        sync_student_transforms(db, student.id)

        # Verify that the outdated TransformedAtom has been deleted and replaced with a new one
        import time
        deadline = time.time() + 5.0
        remaining = []
        while time.time() < deadline:
            db.expire_all()
            remaining = db.scalars(
                select(TransformedAtom).where(TransformedAtom.student_id == student.id)
            ).all()
            if len(remaining) == 1:
                break
            time.sleep(0.1)

        assert len(remaining) == 1
        assert remaining[0].output_format == "adhd_gamified"


def test_support_endpoints_with_local_fallback(client):
    with SessionLocal() as db:
        # Seed a student, doc, atom and transform
        student = User(email="tutor_t@demo.com", display_name="Tutor Test", role="student")
        db.add(student)
        db.commit()

        # Generate access token for the student
        student_token = create_access_token(student.id, student.role)
        headers = {"Authorization": f"Bearer {student_token}"}

        from app.models import SourceDocument
        doc = SourceDocument(uploaded_by=student.id, file_name="test.txt", file_type="txt", storage_key="test_support_key")
        db.add(doc)
        db.commit()

        atom = CurriculumAtom(document_id=doc.id, sequence_index=1, raw_text="Photosynthesis is how plants make food.")
        db.add(atom)
        db.commit()

        ta = TransformedAtom(
            atom_id=atom.id,
            student_id=student.id,
            adhd_weight=0.1,
            dyslexia_weight=0.9,
            asd_weight=0.1,
            output_format="dyslexia_audio",
            transformed_text="Photosynthesis (plants making food).",
            audio_script="Photosynthesis.",
            llm_model="test_model",
            prompt_version="1.0.0",
            review_status="approved",
        )
        db.add(ta)
        db.commit()

        # Test simplify support request (no question)
        resp = client.post(f"/transforms/{ta.id}/support", json={}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "simpler summary" in data["response"]

        # Test question support request
        resp = client.post(f"/transforms/{ta.id}/support", json={"question": "What is photosynthesis?"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "What is photosynthesis?" in data["response"]

        # Test submit feedback
        resp = client.post(f"/transforms/{ta.id}/feedback", json={"message": "This section was hard to understand!"}, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["status"] == "success"

        # Verify feedback was stored in DB
        feedback = db.scalar(select(StudentFeedback).where(StudentFeedback.transformed_atom_id == ta.id))
        assert feedback is not None
        assert feedback.message == "This section was hard to understand!"

        # Test educator fetching feedback (need educator authentication)
        teacher = User(email="teacher_t@demo.com", display_name="Teacher Test", role="educator")
        db.add(teacher)
        db.commit()

        teacher_token = create_access_token(teacher.id, teacher.role)
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        # Link doc to teacher's institution/id or make teacher uploader to satisfy access checks
        doc.uploaded_by = teacher.id
        db.commit()

        resp = client.get(f"/analytics/{doc.id}/feedback", headers=teacher_headers)
        assert resp.status_code == 200
        feedback_list = resp.json()
        assert len(feedback_list) == 1
        assert feedback_list[0]["student_name"] == "Tutor Test"
        assert feedback_list[0]["message"] == "This section was hard to understand!"
        assert feedback_list[0]["sequence_index"] == 1
