"""End-to-end: upload -> ingest -> quiz -> transform -> review -> deliver -> signals."""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient

SAMPLE_TEXT = (
    "Photosynthesis is the process by which green plants make food using sunlight. "
    "It takes place in the chloroplasts of plant cells. Plants take in carbon dioxide "
    "and water. They use light energy to turn these into glucose and oxygen. The oxygen "
    "is released into the air. Animals breathe this oxygen to stay alive. Define the key "
    "stages of photosynthesis and explain why it matters for life on Earth."
)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _poll_parse(client: TestClient, token: str, doc_id: str, timeout: float = 15.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/documents/{doc_id}/status", headers=_auth(token))
        body = resp.json()
        if body["parse_status"] in ("complete", "failed"):
            return body
        time.sleep(0.2)
    raise AssertionError("parse did not finish in time")


def test_health(client: TestClient):
    assert client.get("/health").json()["status"] == "ok"


def test_full_pipeline(client: TestClient, educator_token: str, student: dict):
    # 1. Educator uploads a document.
    files = {"file": ("lesson.txt", io.BytesIO(SAMPLE_TEXT.encode()), "text/plain")}
    up = client.post("/documents", files=files, headers=_auth(educator_token))
    assert up.status_code == 202, up.text
    doc_id = up.json()["document_id"]

    # 2. Ingestion completes (runs in background thread).
    status = _poll_parse(client, educator_token, doc_id)
    assert status["parse_status"] == "complete"
    assert status["atom_count"] >= 1

    # 3. Student completes the onboarding quiz (dyslexia-leaning).
    quiz_answers = {
        "q1": "never", "q2": "always", "q3": "never", "q4": "always", "q5": "never",
        "q6": "never", "q7": "never", "q8": "always", "q9": "never", "q10": "never",
    }
    pr = client.post(
        f"/profiles/{student['id']}/quiz",
        json={"answers": quiz_answers},
        headers=_auth(student["token"]),
    )
    assert pr.status_code == 200, pr.text
    assert pr.json()["dyslexia_weight"] > pr.json()["adhd_weight"]

    # 4. Student prepares their own material → self-study, auto-approved (no
    #    educator review gate).
    tr = client.post(
        "/transforms",
        json={"document_id": doc_id},
        headers=_auth(student["token"]),
    )
    assert tr.status_code == 202, tr.text
    assert tr.json()["review_required"] is False

    # 5. Content is committed per-atom; poll until it appears.
    deadline = time.time() + 15
    content: dict = {"atoms": []}
    while time.time() < deadline:
        content = client.get(
            f"/transforms?document_id={doc_id}", headers=_auth(student["token"])
        ).json()
        if content["atoms"]:
            break
        time.sleep(0.2)
    assert content["atoms"], "student should receive auto-approved atoms"
    first = content["atoms"][0]
    assert first["review_status"] == "auto_approved"
    assert first["output_format"] == "dyslexia_audio"
    # Content must not be truncated mid-word or empty.
    assert len(first["transformed_text"]) > 20

    # 7. Student starts a session and records signals.
    sess = client.post(
        "/sessions", json={"document_id": doc_id}, headers=_auth(student["token"])
    ).json()
    ev = client.post(
        f"/sessions/{sess['id']}/events",
        json={
            "atom_id": first["atom_id"],
            "transformed_atom_id": first["id"],
            "event_type": "atom_complete",
            "time_on_atom_ms": 30000,
            "retry_count": 0,
        },
        headers=_auth(student["token"]),
    )
    assert ev.status_code == 204

    # 8. Educator can read analytics for the document.
    analytics = client.get(f"/analytics/{doc_id}", headers=_auth(educator_token))
    assert analytics.status_code == 200
    assert isinstance(analytics.json(), list)


def test_educator_initiated_transform_requires_review(client: TestClient, educator_token: str, student: dict):
    # Give the student a profile.
    client.post(
        f"/profiles/{student['id']}/quiz",
        json={"answers": {f"q{i}": "never" for i in range(1, 11)} | {"q3": "always", "q6": "always"}},
        headers=_auth(student["token"]),
    )
    files = {"file": ("lesson2.txt", io.BytesIO(SAMPLE_TEXT.encode()), "text/plain")}
    doc_id = client.post("/documents", files=files, headers=_auth(educator_token)).json()["document_id"]
    _poll_parse(client, educator_token, doc_id)

    # Educator requests a transform FOR the student → must go through review.
    tr = client.post(
        "/transforms",
        json={"document_id": doc_id, "student_id": student["id"]},
        headers=_auth(educator_token),
    )
    assert tr.status_code == 202, tr.text
    assert tr.json()["review_required"] is True

    # It appears in the educator's review queue as pending.
    deadline = time.time() + 15
    total = 0
    while time.time() < deadline:
        total = client.get("/transforms/review-queue", headers=_auth(educator_token)).json()["total"]
        if total >= 1:
            break
        time.sleep(0.2)
    assert total >= 1, "educator-initiated transforms must be reviewable"
