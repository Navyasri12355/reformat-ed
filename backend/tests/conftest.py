"""Pytest fixtures. Sets an isolated SQLite DB + temp storage BEFORE app import."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Must run before any `app.*` import so pydantic Settings picks these up.
_TMP = Path(tempfile.mkdtemp(prefix="neuracore-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = (_TMP / "storage").as_posix()
os.environ["TASK_BACKEND"] = "inline"
os.environ["OPENAI_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db() -> None:
    init_db()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def educator_token(client: TestClient) -> str:
    email = f"edu-{os.urandom(4).hex}@school.test"
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "display_name": "Edu", "role": "educator"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def student(client: TestClient) -> dict:
    email = f"stu-{os.urandom(4).hex}@school.test"
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "display_name": "Stu", "role": "student"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    return {"token": token, "id": me["id"]}
