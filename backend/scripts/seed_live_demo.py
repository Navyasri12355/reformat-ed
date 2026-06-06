"""Drive the *running* API to produce approved, ready-to-view content.

Usage (backend must be running on the given base URL):
    python scripts/seed_live_demo.py [profile]   # profile: asd | adhd | dyslexia

Prints a JSON line with the student tokens and document id so a browser session
can jump straight into the learning view.
"""

from __future__ import annotations

import io
import json
import sys
import time

import httpx

BASE = "http://localhost:8000"

SAMPLE = (
    "Photosynthesis is how green plants make their own food using sunlight. "
    "It happens inside chloroplasts, which contain a green colour called chlorophyll. "
    "For a plant, making food this way is a piece of cake. "
    "The plant takes in carbon dioxide from the air and water from the soil. "
    "It uses light energy to make glucose, a sugar it uses as food. "
    "It also releases oxygen into the air, which animals breathe to stay alive. "
    "Define the main stages of photosynthesis and explain why it matters."
)

# Quiz answers that make each trait dominant (q1-q4 ADHD, q5-q8 dyslexia, q9-q12 ASD).
QUIZ = {
    "adhd": {f"q{i}": "always" for i in (1, 2, 3, 4)},
    "dyslexia": {f"q{i}": "always" for i in (5, 6, 7, 8)},
    "asd": {f"q{i}": "always" for i in (9, 10, 11, 12)},
}


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "asd"
    nonce = str(int(time.time()))
    c = httpx.Client(base_url=BASE, timeout=30)

    # Educator
    edu = c.post("/auth/register", json={
        "email": f"edu-{nonce}@demo.test", "password": "password123",
        "display_name": "Demo Teacher", "role": "educator",
    }).json()
    eh = {"Authorization": f"Bearer {edu['access_token']}"}

    # Upload
    files = {"file": (f"lesson-{nonce}.txt", io.BytesIO(SAMPLE.encode()), "text/plain")}
    up = c.post("/documents", files=files, headers=eh).json()
    doc_id = up["document_id"]
    for _ in range(60):
        st = c.get(f"/documents/{doc_id}/status", headers=eh).json()
        if st["parse_status"] in ("complete", "failed"):
            break
        time.sleep(0.25)

    # Student + profile
    stu = c.post("/auth/register", json={
        "email": f"stu-{profile}-{nonce}@demo.test", "password": "password123",
        "display_name": f"Demo {profile.upper()} Student", "role": "student",
    }).json()
    sh = {"Authorization": f"Bearer {stu['access_token']}"}
    me = c.get("/auth/me", headers=sh).json()
    answers = {q: "never" for q in [f"q{i}" for i in range(1, 11)]}
    answers.update(QUIZ[profile])
    c.post(f"/profiles/{me['id']}/quiz", json={"answers": answers}, headers=sh)

    # Transform (as student) then approve everything (as educator)
    c.post("/transforms", json={"document_id": doc_id}, headers=sh)
    for _ in range(60):
        q = c.get("/transforms/review-queue", headers=eh).json()
        if q["total"] > 0:
            break
        time.sleep(0.25)
    q = c.get("/transforms/review-queue?page=1", headers=eh).json()
    for item in q["items"]:
        c.post(f"/transforms/{item['transformed_atom_id']}/review",
               json={"action": "approve"}, headers=eh)

    print(json.dumps({
        "document_id": doc_id,
        "student_access": stu["access_token"],
        "student_refresh": stu["refresh_token"],
        "profile": profile,
    }))


if __name__ == "__main__":
    main()
