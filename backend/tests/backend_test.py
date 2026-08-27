"""Backend API tests for AI Study Assistant."""
import os
import io
import json
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # fallback from frontend .env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@studyai.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def student_session():
    s = requests.Session()
    email = f"TEST_student_{uuid.uuid4().hex[:8]}@test.com"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "test1234", "name": "Test Student"}, timeout=30)
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    s.email = email
    return s


@pytest.fixture(scope="session")
def uploaded_doc_id(admin_session):
    text_content = b"Photosynthesis is the process by which green plants use sunlight to synthesize foods with the help of chlorophyll. It converts carbon dioxide and water into glucose and oxygen. This process occurs primarily in the chloroplasts of plant cells."
    files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
    r = admin_session.post(f"{API}/documents/upload", files=files, timeout=60)
    assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text}"
    data = r.json()
    assert "id" in data
    return data["id"]


# --- AUTH ---
class TestAuth:
    def test_login_admin(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert "id" in data
        assert "password_hash" not in data
        assert "access_token" in s.cookies

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrongpass"}, timeout=15)
        assert r.status_code == 401

    def test_register_and_me(self):
        s = requests.Session()
        email = f"TEST_user_{uuid.uuid4().hex[:8]}@test.com"
        r = s.post(f"{API}/auth/register", json={"email": email, "password": "pw123456", "name": "Foo Bar"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == email.lower()
        assert data["onboarded"] is False

        me = s.get(f"{API}/auth/me", timeout=15)
        assert me.status_code == 200
        assert me.json()["email"] == email.lower()

    def test_register_duplicate(self, admin_session):
        r = requests.post(f"{API}/auth/register", json={"email": ADMIN_EMAIL, "password": "whatever", "name": "x"}, timeout=15)
        assert r.status_code == 400

    def test_me_unauth(self):
        r = requests.get(f"{API}/auth/me", timeout=15)
        assert r.status_code == 401

    def test_logout(self, admin_session):
        s = requests.Session()
        s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        r = s.post(f"{API}/auth/logout", timeout=15)
        assert r.status_code == 200

    def test_onboarding(self, student_session):
        payload = {
            "grade_level": "12",
            "subjects": ["Math", "Physics"],
            "curriculum": "IB",
            "exam_dates": [],
            "daily_study_goal": 90
        }
        r = student_session.post(f"{API}/auth/onboarding", json=payload, timeout=15)
        assert r.status_code == 200
        me = student_session.get(f"{API}/auth/me", timeout=15)
        assert me.json().get("onboarded") is True
        assert me.json().get("curriculum") == "IB"


# --- DOCUMENTS ---
class TestDocuments:
    def test_upload_txt(self, uploaded_doc_id):
        assert uploaded_doc_id

    def test_list_documents(self, admin_session, uploaded_doc_id):
        r = admin_session.get(f"{API}/documents", timeout=15)
        assert r.status_code == 200
        docs = r.json()
        assert isinstance(docs, list)
        assert any(d.get("id") == uploaded_doc_id for d in docs)
        # ensure no mongo _id
        for d in docs:
            assert "_id" not in d

    def test_get_single_document(self, admin_session, uploaded_doc_id):
        r = admin_session.get(f"{API}/documents/{uploaded_doc_id}", timeout=15)
        assert r.status_code == 200
        doc = r.json()
        assert "_id" not in doc
        assert doc.get("id") == uploaded_doc_id
        assert doc.get("original_filename") is not None

    def test_get_document_not_found(self, admin_session):
        r = admin_session.get(f"{API}/documents/nonexistent-id", timeout=15)
        assert r.status_code == 404

    def test_list_documents_all_have_id(self, admin_session, uploaded_doc_id):
        """RETEST: every document in list must have 'id' field."""
        r = admin_session.get(f"{API}/documents", timeout=15)
        assert r.status_code == 200
        docs = r.json()
        assert len(docs) > 0
        for d in docs:
            assert "id" in d, f"Doc missing 'id': {d}"
            assert d["id"], "id must not be empty"
            assert "_id" not in d


# --- AI ---
class TestAI:
    def test_generate_summary(self, admin_session, uploaded_doc_id):
        r = admin_session.post(f"{API}/ai/summary",
                               json={"document_id": uploaded_doc_id, "summary_type": "short"}, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("content"), "Summary content should not be empty"
        assert data.get("summary_type") == "short"

    def test_generate_quiz(self, admin_session, uploaded_doc_id):
        r = admin_session.post(f"{API}/ai/quiz", json={
            "document_ids": [uploaded_doc_id],
            "question_types": ["multiple_choice"],
            "difficulty": "easy",
            "num_questions": 3
        }, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "quiz_data" in data
        qd = data["quiz_data"]
        # allow tolerance: either questions parsed OR error field indicating LLM issue
        assert "questions" in qd

    def test_generate_flashcards(self, admin_session, uploaded_doc_id):
        r = admin_session.post(f"{API}/ai/flashcards", json={"document_id": uploaded_doc_id}, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "flashcards" in data
        assert isinstance(data["flashcards"], list)


# --- DASHBOARD & PROGRESS ---
class TestDashboard:
    def test_progress_stats(self, admin_session):
        r = admin_session.get(f"{API}/progress/stats", timeout=15)
        assert r.status_code == 200
        data = r.json()
        for key in ["documents_uploaded", "quizzes_taken", "flashcards_created",
                    "current_streak", "longest_streak", "total_study_minutes"]:
            assert key in data

    def test_dashboard(self, admin_session, uploaded_doc_id):
        r = admin_session.get(f"{API}/dashboard", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "recent_documents" in data
        assert "stats" in data
        assert "study_plan" in data
        # RETEST: recent_documents each has 'id'
        for d in data["recent_documents"]:
            assert "id" in d and d["id"], f"recent doc missing id: {d}"
            assert "_id" not in d

    def test_list_flashcards_have_id(self, admin_session, uploaded_doc_id):
        """RETEST: flashcards list items must have 'id'."""
        r = admin_session.get(f"{API}/flashcards", timeout=15)
        assert r.status_code == 200
        cards = r.json()
        assert isinstance(cards, list)
        for f in cards:
            assert "id" in f and f["id"]
            assert "_id" not in f

    def test_study_plan_current_has_id_when_present(self, admin_session):
        """RETEST: study-plan/current returns 'id' when a plan exists."""
        # Ensure at least one exists — try to fetch; if empty, generate one quickly is skipped (LLM cost)
        r = admin_session.get(f"{API}/study-plan/current", timeout=15)
        assert r.status_code == 200
        data = r.json()
        # If a plan exists, it must have 'id'; empty stub is allowed
        if data.get("plan_data") and data.get("user_id"):
            assert "id" in data and data["id"]
            assert "_id" not in data

    def test_log_activity_creates_streak_when_missing(self):
        """RETEST: POST /progress/log-activity works when streak doc doesn't exist."""
        s = requests.Session()
        email = f"TEST_streak_{uuid.uuid4().hex[:8]}@test.com"
        rr = s.post(f"{API}/auth/register", json={"email": email, "password": "pw123456", "name": "Streak User"}, timeout=15)
        assert rr.status_code == 200
        # NO onboarding call -> streak doc does not exist
        r = s.post(f"{API}/progress/log-activity", json={"study_minutes": 15}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("current_streak") == 1
        # verify persistence via stats
        stats = s.get(f"{API}/progress/stats", timeout=15).json()
        assert stats["current_streak"] == 1
        assert stats["total_study_minutes"] == 15


# --- NOTES ---
class TestNotes:
    def test_create_and_get_note(self, admin_session):
        payload = {"title": "TEST_note", "content": "hello world", "tags": ["a"], "color": "mint", "is_pinned": False}
        r = admin_session.post(f"{API}/notes", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        n = r.json()
        assert n["id"] and "_id" not in n
        assert n["title"] == "TEST_note"
        assert n["color"] == "mint"
        # GET single
        g = admin_session.get(f"{API}/notes/{n['id']}", timeout=15)
        assert g.status_code == 200
        assert g.json()["id"] == n["id"]

    def test_list_notes_pinned_first(self, admin_session):
        # create pinned + unpinned
        r1 = admin_session.post(f"{API}/notes", json={"title": "TEST_unpinned", "content": "x", "color": "butter", "is_pinned": False}).json()
        time.sleep(0.05)
        r2 = admin_session.post(f"{API}/notes", json={"title": "TEST_pinned", "content": "y", "color": "peach", "is_pinned": True}).json()
        lr = admin_session.get(f"{API}/notes", timeout=15)
        assert lr.status_code == 200
        lst = lr.json()
        assert isinstance(lst, list)
        for n in lst:
            assert "id" in n and "_id" not in n
        pinned_ids = [n["id"] for n in lst if n["is_pinned"]]
        unpinned_ids = [n["id"] for n in lst if not n["is_pinned"]]
        # r2 (pinned) should appear before r1 (unpinned)
        idx_pinned = next(i for i, n in enumerate(lst) if n["id"] == r2["id"])
        idx_unpinned = next(i for i, n in enumerate(lst) if n["id"] == r1["id"])
        assert idx_pinned < idx_unpinned

    def test_update_note(self, admin_session):
        r = admin_session.post(f"{API}/notes", json={"title": "TEST_upd", "content": "old", "color": "lavender"}).json()
        u = admin_session.put(f"{API}/notes/{r['id']}", json={"title": "TEST_upd2", "content": "new", "color": "orange", "is_pinned": True})
        assert u.status_code == 200
        assert u.json()["title"] == "TEST_upd2"
        assert u.json()["is_pinned"] is True
        g = admin_session.get(f"{API}/notes/{r['id']}").json()
        assert g["content"] == "new"
        assert g["color"] == "orange"

    def test_delete_note(self, admin_session):
        r = admin_session.post(f"{API}/notes", json={"title": "TEST_del", "content": "bye"}).json()
        d = admin_session.delete(f"{API}/notes/{r['id']}")
        assert d.status_code == 200
        g = admin_session.get(f"{API}/notes/{r['id']}")
        assert g.status_code == 404

    def test_note_user_isolation(self, admin_session):
        r = admin_session.post(f"{API}/notes", json={"title": "TEST_iso", "content": "secret"}).json()
        # create another user
        s = requests.Session()
        email = f"TEST_noteiso_{uuid.uuid4().hex[:8]}@test.com"
        rr = s.post(f"{API}/auth/register", json={"email": email, "password": "pw123456", "name": "Iso"})
        assert rr.status_code == 200
        g = s.get(f"{API}/notes/{r['id']}")
        assert g.status_code == 404
        u = s.put(f"{API}/notes/{r['id']}", json={"title": "hack", "content": "x"})
        assert u.status_code == 404
        d = s.delete(f"{API}/notes/{r['id']}")
        assert d.status_code == 404
        lst = s.get(f"{API}/notes").json()
        assert all(n["id"] != r["id"] for n in lst)

    def test_notes_unauthenticated(self):
        r = requests.get(f"{API}/notes")
        assert r.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
