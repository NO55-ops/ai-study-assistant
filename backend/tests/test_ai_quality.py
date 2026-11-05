import importlib.util
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("backend_server", ROOT / "server.py")
backend_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backend_server)


def test_app_health_and_readiness_are_exposed():
    health = backend_server.app.routes
    health_paths = {route.path for route in health}
    assert "/health" in health_paths
    assert "/ready" in health_paths

    ready_route = next(route for route in health if route.path == "/ready")
    assert callable(ready_route.endpoint)


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


def test_generate_study_plan_creates_structured_schedule(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))
    monkeypatch.setattr(backend_server, "llm_generate", AsyncMock(return_value='```json\n{"weeks":[{"week_number":1,"days":[{"day":"Monday","tasks":[{"subject":"Math","topic":"Algebra","duration_minutes":45,"task_type":"revision"}]}]}]}\n```'))

    req = backend_server.StudyPlanRequest(
        title="Math exam prep",
        subject="Mathematics",
        topics=["Algebra", "Geometry"],
        goal="Score 85%",
        exam_date="2026-12-15",
        available_days=["Monday", "Wednesday", "Friday"],
        daily_study_time=60,
        weeks_count=2,
    )

    result = asyncio.run(backend_server.generate_study_plan(req, request=None))
    assert result["user_id"] == "user-1"
    assert result["plan_data"]["weeks"][0]["days"][0]["tasks"][0]["subject"] == "Math"
    assert result["plan_data"]["goal"] == "Score 85%"
    assert result["plan_data"]["title"] == "Math exam prep"


def test_generate_study_plan_falls_back_when_ai_response_is_invalid(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1"}))
    monkeypatch.setattr(backend_server, "llm_generate", AsyncMock(return_value='not-json'))

    req = backend_server.StudyPlanRequest(
        title="Biology plan",
        subject="Biology",
        topics=["Cell structure"],
        goal="Improve recall",
        exam_date="2026-11-20",
        available_days=["Tuesday", "Thursday"],
        daily_study_time=45,
        weeks_count=1,
    )

    result = asyncio.run(backend_server.generate_study_plan(req, request=None))
    assert result["plan_data"]["weeks"][0]["days"][0]["tasks"]
    assert result["plan_data"]["goal"] == "Improve recall"


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


def test_parse_mark_scheme_extracts_official_points_only():
    scheme_text = """
    1 (a) State the function of ATP. [2]
    Award 1 mark for 'stores/releases energy' and 1 mark for 'used in cellular processes'.
    Accept 'energy for metabolism' as equivalent to 'stores/releases energy'.
    1 (b) Explain why the cell membrane is selectively permeable. [3]
    Award 1 mark for 'lipid bilayer'; 1 mark for 'controls movement of substances'; 1 mark for 'allows small/non-polar molecules to pass'.
    """

    parsed = backend_server.parse_mark_scheme_text(scheme_text)
    assert parsed["questions"][0]["marks_total"] == 2
    assert any("stores/releases energy" in point.lower() for point in parsed["questions"][0]["marking_points"])
    assert parsed["questions"][0]["accepted_alternatives"]
    assert parsed["unreliable"] == []


def test_mark_exam_answer_awards_partial_credit_with_feedback():
    question = {
        "question_ref": "1(a)",
        "marks_total": 3,
        "marking_points": [
            "stores/releases energy",
            "used in cellular processes",
            "cell respiration"
        ],
        "accepted_alternatives": [
            "energy for metabolism"
        ],
    }

    result = backend_server.mark_exam_answer(question, "energy for metabolism and it is used in cell respiration")
    assert result["awarded_marks"] >= 2
    assert result["awarded_marks"] <= 3
    assert "marks awarded" in result["feedback"].lower()
    assert "expected answer" in result["feedback"].lower()
    assert result["misconceptions"]


def test_extract_concepts_and_assessments_with_user_isolation():
    document_text = """
    Photosynthesis is the process by which plants convert light energy into chemical energy.
    Chlorophyll absorbs light in the thylakoid membranes. Glucose is produced in the Calvin cycle.
    The process depends on water, carbon dioxide, and light. Photosynthesis supports plant growth and respiration.
    """

    concepts = backend_server.extract_concepts_from_document(document_text, document_title="Photosynthesis notes")
    assert concepts["concepts"]
    assert any("photosynthesis" in concept["name"].lower() for concept in concepts["concepts"])
    assert concepts["relationships"]

    assessment = backend_server.generate_concept_assessment(concepts["concepts"][0], "short")
    assert assessment["prompt"]
    assert assessment["difficulty"]

    progress = backend_server.save_concept_map_progress("user-1", {"map_id": "map-1", "concept_id": "concept-1", "status": "weak"})
    assert progress["user_id"] == "user-1"
    assert progress["status"] == "weak"

    isolated = backend_server.get_concept_map_progress("user-2", "map-1")
    assert isolated == []


def test_adaptive_learning_profile_and_retention_are_calculated_from_real_activity():
    backend_server.MEMORY_STORE.clear()
    backend_server.MEMORY_STORE.setdefault("quiz_attempts", [])
    backend_server.MEMORY_STORE["quiz_attempts"].extend([
        {"user_id": "user-1", "completed_at": "2024-05-10T09:00:00Z", "score": 92, "topic": "Photosynthesis"},
        {"user_id": "user-1", "completed_at": "2024-05-11T09:00:00Z", "score": 76, "topic": "Photosynthesis"},
        {"user_id": "user-1", "completed_at": "2024-05-12T09:00:00Z", "score": 55, "topic": "Cell respiration"},
    ])
    backend_server.MEMORY_STORE.setdefault("mock_exam_attempts", [])
    backend_server.MEMORY_STORE["mock_exam_attempts"].extend([
        {"user_id": "user-1", "exam_id": "exam-1", "percentage": 82, "topic": "Photosynthesis", "created_at": "2024-05-12T18:00:00Z"},
        {"user_id": "user-1", "exam_id": "exam-2", "percentage": 64, "topic": "Cell respiration", "created_at": "2024-05-13T18:00:00Z"},
    ])
    backend_server.MEMORY_STORE.setdefault("flashcard_sets", [])
    backend_server.MEMORY_STORE["flashcard_sets"].extend([
        {"user_id": "user-1", "name": "Bio deck", "mastery_score": 88, "flashcards": [{"front": "Q", "back": "A"}], "created_at": "2024-05-12T12:00:00Z"},
        {"user_id": "user-1", "name": "Resp deck", "mastery_score": 52, "flashcards": [{"front": "Q1", "back": "A1"}], "created_at": "2024-05-13T10:00:00Z"},
    ])
    backend_server.MEMORY_STORE.setdefault("study_sessions", [])
    backend_server.MEMORY_STORE["study_sessions"].extend([
        {"user_id": "user-1", "started_at": "2024-05-12T10:00:00Z", "ended_at": "2024-05-12T11:00:00Z", "duration_minutes": 60, "session_type": "study", "date_local": "2024-05-12"},
        {"user_id": "user-1", "started_at": "2024-05-13T09:00:00Z", "ended_at": "2024-05-13T10:00:00Z", "duration_minutes": 60, "session_type": "study", "date_local": "2024-05-13"},
    ])

    profile = backend_server.build_adaptive_learning_profile("user-1")
    assert profile["mastered_concepts"]
    assert profile["developing_concepts"]
    assert "Photosynthesis" in profile["mastered_concepts"]
    assert "Cell respiration" in profile["developing_concepts"] or "Cell respiration" in profile["needs_attention"]

    retention = backend_server.estimate_retention("user-1")
    assert retention
    assert any(item["concept"] == "Photosynthesis" for item in retention)
    assert retention[0]["estimated_need_for_revision"] in {"low", "medium", "high"}


def test_adaptive_difficulty_and_misconception_detection_use_real_history():
    backend_server.MEMORY_STORE.clear()
    backend_server.MEMORY_STORE.setdefault("quiz_attempts", [])
    backend_server.MEMORY_STORE["quiz_attempts"].extend([
        {"user_id": "user-2", "completed_at": "2024-05-14T09:00:00Z", "score": 30, "topic": "Photosynthesis", "question_id": "q1"},
        {"user_id": "user-2", "completed_at": "2024-05-15T09:00:00Z", "score": 20, "topic": "Photosynthesis", "question_id": "q2"},
        {"user_id": "user-2", "completed_at": "2024-05-16T09:00:00Z", "score": 80, "topic": "Light energy", "question_id": "q3"},
    ])
    backend_server.MEMORY_STORE.setdefault("mock_exam_attempts", [])
    backend_server.MEMORY_STORE["mock_exam_attempts"].extend([
        {"user_id": "user-2", "exam_id": "exam-b", "percentage": 42, "created_at": "2024-05-15T12:00:00Z", "question_results": [{"topic": "Photosynthesis", "misconceptions": ["Confusing chlorophyll with sunlight absorption"]}]},
    ])

    plan = backend_server.build_adaptive_question_plan("user-2", "Photosynthesis")
    assert plan["recommended_difficulty"] in {"foundation", "intermediate", "advanced"}
    assert isinstance(plan["prerequisite_concepts"], list)

    misconceptions = backend_server.detect_misconceptions("user-2")
    assert misconceptions
    assert any(item["underlying_concept"] or item["concept"] for item in misconceptions)


def test_adaptive_learning_path_and_user_isolation():
    backend_server.MEMORY_STORE.clear()
    backend_server.MEMORY_STORE.setdefault("mock_exam_attempts", [])
    backend_server.MEMORY_STORE["mock_exam_attempts"].extend([
        {"user_id": "user-1", "exam_id": "exam-a", "percentage": 68, "created_at": "2024-05-18T12:00:00Z"},
        {"user_id": "user-2", "exam_id": "exam-b", "percentage": 89, "created_at": "2024-05-18T12:00:00Z"},
    ])
    backend_server.MEMORY_STORE.setdefault("flashcard_sets", [])
    backend_server.MEMORY_STORE["flashcard_sets"].extend([
        {"user_id": "user-1", "mastery_score": 58, "name": "Core bio", "flashcards": [{"front": "x", "back": "y"}]},
        {"user_id": "user-2", "mastery_score": 88, "name": "Strong biology", "flashcards": [{"front": "x", "back": "y"}]},
    ])

    path_for_user_1 = backend_server.build_learning_path("user-1", "Biology exam prep")
    path_for_user_2 = backend_server.build_learning_path("user-2", "Biology exam prep")
    assert path_for_user_1
    assert path_for_user_2
    assert path_for_user_1[0]["title"]
    assert path_for_user_1[0]["estimated_minutes"] > 0
    assert any(item["title"] != path_for_user_2[0]["title"] or item["estimated_minutes"] != path_for_user_2[0]["estimated_minutes"] for item in path_for_user_1[:1])


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


def test_library_topic_payload_flattens_resource_content():
    class FakeDb:
        rows = {
            "library_qualifications": [{"slug": "cambridge-igcse", "name": "Cambridge IGCSE", "status": "published"}],
            "library_subjects": [{"slug": "international-mathematics-0607-extended", "qualification_slug": "cambridge-igcse", "name": "International Mathematics 0607 Extended", "status": "published"}],
            "library_topics": [{"slug": "quadratic-equations", "subject_slug": "international-mathematics-0607-extended", "title": "Quadratic Equations", "status": "published"}],
            "library_resources": [
                {"slug": "quadratic-equations-summary", "topic_slug": "quadratic-equations", "resource_type": "summary", "title": "Quadratic Equations summary", "status": "published", "payload": {"content": "Factorise or use the formula."}},
                {"slug": "quadratic-equations-notes", "topic_slug": "quadratic-equations", "resource_type": "notes", "title": "Notes", "status": "published", "payload": {"notes": [{"heading": "Definition and standard form", "content": ["A quadratic equation is any equation that can be written in the form ax^2 + bx + c = 0."]}]}} ,
            ],
        }

    catalog = backend_server.get_published_library_catalog(db=FakeDb())
    topic = catalog["qualifications"][0]["subjects"][0]["topics"][0]
    assert "notes" in topic
    assert topic["notes"][0]["heading"] == "Definition and standard form"
    assert "summary" in topic or topic["resources"][0]["title"] == "Quadratic Equations summary"


def test_admin_library_catalog_requires_admin(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    monkeypatch.setattr(backend_server, "get_current_user", AsyncMock(return_value={"id": "user-1", "role": "student"}))

    try:
        asyncio.run(backend_server.get_admin_library_catalog(request=None))
        raise AssertionError("Expected admin-only access to be rejected")
    except backend_server.HTTPException as exc:
        assert exc.status_code == 403


def test_streak_summary_accounts_for_missed_days_and_duplicate_day_sessions():
    sessions = [
        {"started_at": "2026-10-01T09:00:00Z", "ended_at": "2026-10-01T10:00:00Z", "duration_minutes": 60},
        {"started_at": "2026-10-02T09:00:00Z", "ended_at": "2026-10-02T10:00:00Z", "duration_minutes": 60},
        {"started_at": "2026-10-02T18:00:00Z", "ended_at": "2026-10-02T18:30:00Z", "duration_minutes": 30},
        {"started_at": "2026-10-04T08:00:00Z", "ended_at": "2026-10-04T09:00:00Z", "duration_minutes": 60},
    ]

    summary = backend_server.calculate_streak_summary(sessions=sessions, timezone_name="UTC")
    assert summary["total_active_days"] == 3
    assert summary["current_streak"] == 1
    assert summary["longest_streak"] == 2
    assert summary["active_days"] == ["2026-10-01", "2026-10-02", "2026-10-04"]


def test_daily_goal_progress_tracks_today_minutes_and_remaining_goal():
    goal = backend_server.build_daily_goal_progress(
        daily_goal_minutes=90,
        sessions=[
            {"started_at": "2026-10-23T09:00:00Z", "ended_at": "2026-10-23T10:30:00Z", "duration_minutes": 90},
            {"started_at": "2026-10-23T18:00:00Z", "ended_at": "2026-10-23T18:15:00Z", "duration_minutes": 15},
        ],
        today_iso="2026-10-23",
    )

    assert goal["minutes_completed"] == 105
    assert goal["minutes_remaining"] == 0
    assert goal["progress_percent"] == 100
    assert goal["goal_reached"] is True


def test_build_learning_analytics_uses_real_study_and_mock_exam_data(monkeypatch):
    backend_server.MEMORY_STORE.clear()
    backend_server.MEMORY_STORE["mock_exam_attempts"] = [{
        "id": "attempt-1",
        "user_id": "u-1",
        "exam_id": "exam-1",
        "percentage": 72,
        "total_marks": 18,
        "max_marks": 25,
        "created_at": "2026-10-24T09:00:00Z",
    }]
    backend_server.MEMORY_STORE["mock_exams"] = [{
        "id": "exam-1",
        "user_id": "u-1",
        "questions": [{"topic": "Photosynthesis", "difficulty": "medium"}],
    }]

    class FakeFindResult:
        def __init__(self, rows):
            self.rows = rows

        async def to_list(self, limit):
            return self.rows

    monkeypatch.setattr(backend_server.db.documents, "count_documents", AsyncMock(return_value=4))
    monkeypatch.setattr(backend_server.db.quizzes, "count_documents", AsyncMock(return_value=3))
    monkeypatch.setattr(backend_server.db.flashcard_sets, "find", lambda query: FakeFindResult([
        {
            "id": "deck-1",
            "user_id": "u-1",
            "name": "Biology deck",
            "flashcards": [
                {"front": "What is photosynthesis?", "back": "A process plants use to turn light into energy"},
                {"front": "Why is sunlight important?", "back": "It provides the light energy"},
            ],
            "mastery_score": 82,
            "review_count": 5,
        }
    ]))

    result = asyncio.run(backend_server.build_learning_analytics({"id": "u-1", "daily_study_goal": 60, "timezone": "UTC"}))
    assert result["documents_uploaded"] == 4
    assert result["quizzes_completed"] == 3
    assert result["flashcards_total"] == 2
    assert result["flashcard_mastery"]["average_mastery"] == 82.0
    assert result["mock_exam_history"][0]["percentage"] == 72
    assert len(result["insights"]) >= 2
    assert result["overall_progress"] >= 0


def test_validate_study_session_rejects_invalid_or_manipulated_durations():
    try:
        backend_server.validate_study_session_payload({"duration_minutes": 0, "started_at": "2026-10-23T09:00:00Z", "ended_at": "2026-10-23T09:30:00Z"})
        raise AssertionError("Expected invalid duration to be rejected")
    except ValueError as exc:
        assert "at least" in str(exc).lower()

    try:
        backend_server.validate_study_session_payload({"duration_minutes": 1200, "started_at": "2026-10-23T09:00:00Z", "ended_at": "2026-10-23T09:30:00Z"})
        raise AssertionError("Expected over-limit duration to be rejected")
    except ValueError as exc:
        assert "too long" in str(exc).lower()


def test_user_activity_filter_keeps_records_isolated_to_logged_in_user():
    sessions = [
        {"user_id": "u-1", "date_local": "2026-10-23", "duration_minutes": 30},
        {"user_id": "u-2", "date_local": "2026-10-23", "duration_minutes": 45},
    ]

    filtered = backend_server.filter_user_study_sessions(sessions, user_id="u-1")
    assert len(filtered) == 1
    assert filtered[0]["user_id"] == "u-1"


def test_streak_summary_handles_timezone_boundary_days():
    sessions = [
        {"started_at": "2026-10-23T23:30:00-05:00", "ended_at": "2026-10-24T00:15:00-05:00", "duration_minutes": 45},
        {"started_at": "2026-10-24T00:30:00-05:00", "ended_at": "2026-10-24T01:00:00-05:00", "duration_minutes": 30},
    ]

    summary = backend_server.calculate_streak_summary(sessions=sessions, timezone_name="America/New_York")
    assert summary["total_active_days"] == 2
    assert summary["active_days"] == ["2026-10-23", "2026-10-24"]


def test_normalize_flashcard_cards_strips_blank_entries_and_preserves_valid_content():
    cards = [
        {"front": "What is photosynthesis?", "back": "A process plants use to make food", "hint": "Think about sunlight"},
        {"front": "", "back": "", "hint": "ignored"},
        {"front": "Why is chlorophyll important?", "back": "It absorbs light energy"},
    ]

    normalized = backend_server.normalize_flashcard_cards(cards)
    assert len(normalized) == 2
    assert normalized[0]["front"] == "What is photosynthesis?"
    assert normalized[1]["hint"] == ""


def test_prepare_mock_exam_payload_validates_question_count_and_types():
    payload = backend_server.prepare_mock_exam_payload({
        "document_id": "doc-1",
        "topic_selection": ["Photosynthesis", "Cell structure"],
        "difficulty": "mixed",
        "question_types": ["multiple_choice", "short_answer", "structured"],
        "num_questions": 4,
        "duration_minutes": 45,
    })

    assert payload["duration_minutes"] == 45
    assert payload["num_questions"] == 4
    assert payload["question_types"] == ["multiple_choice", "short_answer", "structured"]
    assert payload["topic_selection"] == ["Photosynthesis", "Cell structure"]


def test_grade_essay_question_handles_partial_credit_and_model_answer():
    result = backend_server.grade_mock_question_answer(
        question={
            "type": "short_answer",
            "question": "Explain why plants need sunlight.",
            "marks": 4,
            "marking_criteria": ["States that sunlight provides energy for photosynthesis", "Links energy to sugar production"],
            "model_answer": "Sunlight provides the energy for photosynthesis, which helps plants make glucose.",
        },
        user_answer="Sunlight gives plants energy to make food.",
        difficulty="medium",
    )

    assert result["max_marks"] == 4
    assert 0 <= result["awarded_marks"] <= 4
    assert "feedback" in result
    assert "model_answer" in result
    assert "misconceptions" in result
