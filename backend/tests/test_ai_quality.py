import importlib.util
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("backend_server", ROOT / "server.py")
backend_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backend_server)


def test_strip_markdown_fences_removes_code_blocks():
    raw = '```json\n{"questions": [{"type": "multiple_choice"}]}\n```'
    cleaned = backend_server.strip_markdown_fences(raw)
    assert cleaned.startswith('{')
    assert '```' not in cleaned


def test_validate_quiz_payload_rejects_missing_correct_answer():
    payload = {
        "questions": [
            {
                "type": "multiple_choice",
                "question": "What is photosynthesis?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "E",
                "explanation": "The correct answer is A.",
            }
        ]
    }

    try:
        backend_server.validate_quiz_payload(payload)
        raise AssertionError("Expected ValueError for invalid correct answer")
    except ValueError:
        pass


def test_validate_quiz_payload_accepts_valid_question():
    payload = {
        "questions": [
            {
                "type": "multiple_choice",
                "question": "What is the main product of photosynthesis?",
                "options": ["Glucose", "Oxygen", "Carbon dioxide", "Water"],
                "correct_answer": "A",
                "explanation": "Glucose is produced during the process.",
            }
        ]
    }

    validated = backend_server.validate_quiz_payload(payload)
    assert validated["questions"][0]["correct_answer"] == "A"


def test_llm_stream_handles_empty_or_broken_stream_gracefully(monkeypatch):
    class EmptyStream:
        def __aiter__(self):
            async def _gen():
                if False:
                    yield None
            return _gen()

    class BrokenStream:
        def __aiter__(self):
            raise RuntimeError("stream failure")

    async def fake_create(*args, **kwargs):
        return EmptyStream()

    monkeypatch.setattr(backend_server.openai_client.chat.completions, "create", fake_create)

    async def collect():
        out = []
        async for chunk in backend_server.llm_stream("system", "question"):
            out.append(chunk)
        return out

    empty_output = asyncio.run(collect())
    assert any("relevant information" in item for item in empty_output)

    async def broken_create(*args, **kwargs):
        return BrokenStream()

    monkeypatch.setattr(backend_server.openai_client.chat.completions, "create", broken_create)

    async def collect_broken():
        out = []
        async for chunk in backend_server.llm_stream("system", "question"):
            out.append(chunk)
        return out

    broken_output = asyncio.run(collect_broken())
    assert any("unexpectedly" in item for item in broken_output)


def test_create_question_set_accepts_valid_questions(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))

    payload = {
        "name": "Algebra Set",
        "subject": "Math",
        "topic": "Linear equations",
        "difficulty": "easy",
        "question_type": "multiple_choice",
        "questions": [
            {
                "question": "Solve 2x = 10.",
                "type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "Divide both sides by 2.",
            }
        ],
    }

    result = asyncio.run(backend_server.create_question_set(backend_server.QuestionLibrarySetRequest(**payload), request=None))
    assert result["user_id"] == "user-1"
    assert result["name"] == "Algebra Set"
    assert result["questions"][0]["correct_answer"] == "A"


def test_list_question_sets_only_returns_current_user(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))
    backend_server.MEMORY_STORE["question_sets"] = [
        {"id": "set-1", "user_id": "user-1", "name": "Mine", "created_at": "t", "updated_at": "t"},
        {"id": "set-2", "user_id": "user-2", "name": "Other", "created_at": "t", "updated_at": "t"},
    ]
    backend_server.MEMORY_STORE["question_set_questions"] = [
        {"id": "item-1", "user_id": "user-1", "question_set_id": "set-1", "question": "What?", "type": "multiple_choice", "options": ["A", "B"], "correct_answer": "A", "answer": "", "explanation": ""},
        {"id": "item-2", "user_id": "user-2", "question_set_id": "set-2", "question": "Other?", "type": "multiple_choice", "options": ["A", "B"], "correct_answer": "A", "answer": "", "explanation": ""},
    ]

    result = asyncio.run(backend_server.list_question_sets(request=None))
    assert len(result) == 1
    assert result[0]["user_id"] == "user-1"
    assert all(item["user_id"] == "user-1" for item in result[0]["questions"])


def test_create_question_set_rejects_invalid_payload(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))

    payload = {
        "name": "Bad Set",
        "questions": [
            {"question": "Q1", "type": "multiple_choice", "options": ["A"], "correct_answer": "B"}
        ],
    }

    try:
        asyncio.run(backend_server.create_question_set(backend_server.QuestionLibrarySetRequest(**payload), request=None))
        raise AssertionError("Expected invalid payload to be rejected")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400


def test_question_library_requires_auth(monkeypatch):
    backend_server.MEMORY_STORE.clear()

    async def fail_auth(*args, **kwargs):
        raise backend_server.HTTPException(status_code=401, detail="Not authenticated")

    monkeypatch.setattr(backend_server, "get_current_user", fail_auth)
    try:
        asyncio.run(backend_server.list_question_sets(request=None))
        raise AssertionError("Expected authentication error")
    except backend_server.HTTPException as exc:
        assert exc.status_code == 401


def test_update_note_re_checks_owner_before_returning_result(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    note = {
        "id": "note-1",
        "user_id": "user-1",
        "title": "My note",
        "content": "old",
        "tags": ["a"],
        "color": "mint",
        "is_pinned": False,
        "document_id": None,
        "created_at": "now",
        "updated_at": "now",
    }
    backend_server.MEMORY_STORE["notes"] = [note]

    async def fake_find_one(query, projection=None, sort=None):
        if query == {"_id": "note-1", "user_id": "user-1"}:
            return dict(note)
        if query == {"_id": "note-1"}:
            return {**dict(note), "user_id": "user-2", "title": "Other user note"}
        return None

    async def fake_update_one(query, update):
        if query == {"_id": "note-1", "user_id": "user-1"}:
            note.update({"title": "updated", "content": "new content", "updated_at": "later"})
            return type("Result", (), {"matched_count": 1, "modified_count": 1})()
        return type("Result", (), {"matched_count": 0, "modified_count": 0})()

    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))
    monkeypatch.setattr(backend_server.db.notes, "find_one", fake_find_one)
    monkeypatch.setattr(backend_server.db.notes, "update_one", fake_update_one)

    async def run_update():
        return await backend_server.update_note(
            "note-1",
            backend_server.NoteRequest(
                title="updated",
                content="new content",
                tags=["a"],
                color="mint",
                is_pinned=False,
                document_id=None,
            ),
            request=None,
        )

    result = asyncio.run(run_update())
    assert result["user_id"] == "user-1"
    assert result["title"] == "updated"
    assert result["content"] == "new content"


def test_seed_admin_skips_default_credentials_in_production(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    async def run_seed():
        await backend_server.seed_admin()

    asyncio.run(run_seed())
    assert "users" not in backend_server.MEMORY_STORE or not backend_server.MEMORY_STORE["users"]


def test_library_qualifications_require_auth(monkeypatch):
    backend_server.MEMORY_STORE.clear()

    async def fail_auth(*args, **kwargs):
        raise backend_server.HTTPException(status_code=401, detail="Not authenticated")

    monkeypatch.setattr(backend_server, "get_current_user", fail_auth)
    try:
        asyncio.run(backend_server.list_library_qualifications(request=None))
        raise AssertionError("Expected authentication error")
    except backend_server.HTTPException as exc:
        assert exc.status_code == 401


def test_library_catalog_filters_only_published_entries(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "HAS_REAL_SUPABASE", False)
    monkeypatch.setattr(backend_server, "ALLOW_LOCAL_LIBRARY_FALLBACK", True)
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))
    backend_server.MEMORY_STORE["library_catalog"] = {
        "qualifications": [
            {
                "id": "cambridge-igcse",
                "slug": "cambridge-igcse",
                "name": "Cambridge IGCSE",
                "status": "published",
                "subjects": [
                    {
                        "id": "math-0607",
                        "slug": "international-mathematics-0607-extended",
                        "name": "International Mathematics 0607 Extended",
                        "status": "published",
                        "topics": [
                            {
                                "id": "quadratics",
                                "slug": "quadratic-equations",
                                "title": "Quadratic Equations",
                                "status": "published",
                            },
                            {
                                "id": "draft-topic",
                                "slug": "draft-topic",
                                "title": "Draft Topic",
                                "status": "draft",
                            },
                        ],
                    },
                    {
                        "id": "draft-subject",
                        "slug": "draft-subject",
                        "name": "Draft Subject",
                        "status": "draft",
                        "topics": [],
                    },
                ],
            },
            {
                "id": "draft-qualification",
                "slug": "draft-qualification",
                "name": "Draft Qualification",
                "status": "draft",
                "subjects": [],
            },
        ]
    }

    result = asyncio.run(backend_server.list_library_qualifications(request=None))
    assert len(result) == 1
    assert result[0]["slug"] == "cambridge-igcse"
    assert len(result[0]["subjects"]) == 1
    assert result[0]["subjects"][0]["slug"] == "international-mathematics-0607-extended"
    assert len(result[0]["subjects"][0]["topics"]) == 1
    assert result[0]["subjects"][0]["topics"][0]["slug"] == "quadratic-equations"


def test_library_seed_validation_rejects_missing_reference():
    seed = {
        "qualifications": [
            {
                "slug": "cambridge-igcse",
                "name": "Cambridge IGCSE",
                "status": "published",
                "subjects": [
                    {
                        "slug": "math",
                        "name": "Math",
                        "status": "published",
                        "topics": [
                            {
                                "slug": "quadratics",
                                "title": "Quadratics",
                                "status": "published",
                                "resources": [
                                    {
                                        "resource_type": "notes",
                                        "status": "published",
                                        "payload": {"content": ["Example"]},
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    try:
        backend_server.validate_library_seed(seed)
        raise AssertionError("Expected validation to reject seed data with missing required fields")
    except ValueError as exc:
        assert "required" in str(exc).lower()


def test_library_seed_import_is_idempotent(monkeypatch):
    backend_server.MEMORY_STORE.clear()

    seed = {
        "qualifications": [
            {
                "slug": "cambridge-igcse",
                "name": "Cambridge IGCSE",
                "status": "published",
                "subjects": [
                    {
                        "slug": "mathematics",
                        "name": "Mathematics",
                        "status": "published",
                        "topics": [
                            {
                                "slug": "quadratics",
                                "title": "Quadratics",
                                "status": "published",
                                "resources": [
                                    {
                                        "resource_type": "notes",
                                        "title": "Core idea",
                                        "status": "published",
                                        "payload": {"content": ["Quadratics are equations of degree 2."]},
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    class FakeDb:
        def __init__(self):
            self.rows = {"library_qualifications": [], "library_subjects": [], "library_topics": [], "library_resources": []}

        async def find_one(self, query=None, projection=None, sort=None):
            return None

        async def insert_one(self, item):
            table = item["_table"]
            self.rows[table].append(item)
            return item

    fake_db = FakeDb()
    first = backend_server.import_library_seed(seed, db=fake_db)
    second = backend_server.import_library_seed(seed, db=fake_db)

    assert first["qualifications"][0]["slug"] == "cambridge-igcse"
    assert second["qualifications"][0]["slug"] == "cambridge-igcse"
    assert len(fake_db.rows["library_qualifications"]) == 1
    assert len(fake_db.rows["library_subjects"]) == 1
    assert len(fake_db.rows["library_topics"]) == 1
    assert len(fake_db.rows["library_resources"]) == 1
    assert fake_db.rows["library_resources"][0]["status"] == "published"


def test_db_table_rows_accepts_dict_like_query_result():
    class DictLikeCollection:
        def select(self, *args, **kwargs):
            return {"data": [{"slug": "cambridge-igcse", "name": "Cambridge IGCSE"}]}

    class DictLikeDb:
        library_qualifications = DictLikeCollection()

    rows = backend_server._db_table_rows(DictLikeDb(), "library_qualifications")
    assert rows[0]["slug"] == "cambridge-igcse"
    assert rows[0]["name"] == "Cambridge IGCSE"


def test_library_catalog_raises_clear_error_when_db_is_unconfigured(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "ALLOW_LOCAL_LIBRARY_FALLBACK", False)

    class UnconfiguredDb:
        pass

    try:
        backend_server.get_published_library_catalog(db=UnconfiguredDb())
        raise AssertionError("Expected an explicit database configuration error")
    except RuntimeError as exc:
        assert "not configured" in str(exc).lower()


def test_library_catalog_uses_local_fallback_only_when_enabled(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "HAS_REAL_SUPABASE", False)
    monkeypatch.setattr(backend_server, "ALLOW_LOCAL_LIBRARY_FALLBACK", False)
    monkeypatch.setattr(backend_server, "db", None)
    backend_server.MEMORY_STORE["library_catalog"] = {
        "qualifications": [{"slug": "local-only", "name": "Local Only", "status": "published", "subjects": []}]
    }

    try:
        backend_server.get_published_library_catalog(db=None)
        raise AssertionError("Expected fallback guard to reject in-memory fallback while local mode is disabled")
    except RuntimeError as exc:
        assert "local fallback is disabled" in str(exc).lower()


def test_default_catalog_can_be_converted_to_seed():
    seed = backend_server.convert_default_library_catalog_to_seed()
    assert seed["qualifications"][0]["slug"] == "cambridge-igcse"

    topic = seed["qualifications"][0]["subjects"][0]["topics"][0]
    resource_types = {resource["resource_type"] for resource in topic["resources"]}
    assert {"notes", "formulae", "worked_examples", "exam_tips", "common_mistakes", "flashcards", "practice_questions", "summary"}.issubset(resource_types)

    notes_resource = next(resource for resource in topic["resources"] if resource["resource_type"] == "notes")
    assert isinstance(notes_resource["payload"]["notes"], list)
    assert len(notes_resource["payload"]["notes"]) >= 2

    practice_resource = next(resource for resource in topic["resources"] if resource["resource_type"] == "practice_questions")
    assert practice_resource["payload"]["practice_questions"][0]["correct_answer"] == "C"

    summary_resource = next(resource for resource in topic["resources"] if resource["resource_type"] == "summary")
    assert "Factorise or use the formula" in summary_resource["payload"]["content"]


def test_default_catalog_import_pipeline_is_repeatable_and_deterministic():
    class FakeDb:
        def __init__(self):
            self.rows = {
                "library_qualifications": [],
                "library_subjects": [],
                "library_topics": [],
                "library_resources": [],
            }

        async def find_one(self, query=None, projection=None, sort=None):
            return None

        async def insert_one(self, item):
            table = item["_table"]
            self.rows[table].append(item)
            return item

    fake_db = FakeDb()
    seed = backend_server.convert_default_library_catalog_to_seed()

    report_one = backend_server.import_default_library_catalog(seed=seed, db=fake_db)
    report_two = backend_server.import_default_library_catalog(seed=seed, db=fake_db)

    assert report_one["created"]["library_qualifications"] == 1
    assert report_one["created"]["library_resources"] > 0
    assert report_two["skipped"]["library_resources"] > 0
    assert len(fake_db.rows["library_qualifications"]) == 1
    assert len(fake_db.rows["library_subjects"]) == 1
    assert len(fake_db.rows["library_topics"]) == 1
    assert len({resource["slug"] for resource in fake_db.rows["library_resources"]}) == len(fake_db.rows["library_resources"])


def test_library_catalog_raises_clear_error_on_query_failure(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "HAS_REAL_SUPABASE", True)
    monkeypatch.setattr(backend_server, "ALLOW_LOCAL_LIBRARY_FALLBACK", False)

    class BrokenDb:
        rows = {"library_qualifications": [{"slug": "cambridge-igcse", "name": "Cambridge IGCSE", "status": "published"}], "library_subjects": [], "library_topics": [], "library_resources": []}

        class library_qualifications:
            @staticmethod
            def find(*args, **kwargs):
                raise RuntimeError("cannot reach catalog table")

    try:
        backend_server.get_published_library_catalog(db=BrokenDb())
        raise AssertionError("Expected a database query failure to surface as a clear RuntimeError")
    except RuntimeError as exc:
        assert "query failed" in str(exc).lower()
