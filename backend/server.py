from fastapi import FastAPI, APIRouter, File, UploadFile, Request, HTTPException, Response, Header, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

from typing import List, Optional, Dict, Any

try:
    from supabase import create_client, Client
except ModuleNotFoundError:
    create_client = None
    Client = Any

import os
import logging
import certifi
from urllib.parse import urlparse, quote_plus
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import requests
import io
import re
import copy
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from pptx import Presentation
from openai import AsyncOpenAI
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ALLOW_LOCAL_LIBRARY_FALLBACK = os.environ.get("ALLOW_LOCAL_LIBRARY_FALLBACK", "0").strip().lower() in {"1", "true", "yes", "on"}
HAS_REAL_SUPABASE = bool(create_client is not None and SUPABASE_URL and SUPABASE_KEY)

MEMORY_STORE: Dict[str, List[Dict[str, Any]]] = {}

DEFAULT_LIBRARY_CATALOG = {
    "qualifications": [
        {
            "id": "cambridge-igcse",
            "slug": "cambridge-igcse",
            "name": "Cambridge IGCSE",
            "status": "published",
            "long_name": "Cambridge IGCSE",
            "description": "A curriculum review catalog for inquiry-led study, beginning with International Mathematics 0607 Extended.",
            "subjects": [
                {
                    "id": "international-mathematics-0607-extended",
                    "slug": "international-mathematics-0607-extended",
                    "name": "International Mathematics 0607 Extended",
                    "code": "0607",
                    "status": "published",
                    "description": "Useful draft topic notes for revision. Final syllabus alignment should still be checked against the official Cambridge 0607 Extended syllabus for the relevant exam series.",
                    "topics": [
                        {
                            "id": "quadratic-equations",
                            "slug": "quadratic-equations",
                            "title": "Quadratic Equations",
                            "status": "published",
                            "summary": "Solve quadratic equations by factorisation, completing the square, and the quadratic formula, and use the discriminant to interpret the number of real roots.",
                            "syllabus_note": "This is a useful draft for revision and topic study. Final syllabus alignment must be confirmed against the official Cambridge IGCSE International Mathematics 0607 Extended syllabus for the relevant exam series.",
                            "notes": [
                                {
                                    "heading": "Definition and standard form",
                                    "content": [
                                        "A quadratic equation is any equation that can be written in the form ax^2 + bx + c = 0, where a, b, and c are constants and a ≠ 0.",
                                        "The variable x appears squared, so the graph is a parabola and the equation may have 0, 1, or 2 real solutions depending on the discriminant.",
                                        "Before solving, rewrite the equation in standard form so the coefficients are easy to identify."
                                    ]
                                },
                                {
                                    "heading": "Methods for solving",
                                    "content": [
                                        "Factorisation is the quickest method when the expression splits neatly into two linear factors.",
                                        "Completing the square is a useful method when the expression is not easily factorised and helps reveal the vertex form of a parabola.",
                                        "The quadratic formula x = (-b ± √(b^2 - 4ac)) / 2a always works for any quadratic equation with real coefficients."
                                    ]
                                },
                                {
                                    "heading": "Interpreting the roots",
                                    "content": [
                                        "The discriminant Δ = b^2 - 4ac tells you the number of real roots before solving fully.",
                                        "If Δ > 0, the equation has two distinct real roots; if Δ = 0, there is one repeated root; if Δ < 0, there are no real roots in the real number system.",
                                        "The roots correspond to x-intercepts of the parabola y = ax^2 + bx + c."
                                    ]
                                }
                            ],
                            "formulae": [
                                "Standard form: ax^2 + bx + c = 0, where a ≠ 0",
                                "Quadratic formula: x = (-b ± √(b^2 - 4ac)) / 2a",
                                "Discriminant: Δ = b^2 - 4ac",
                                "Sum of roots: -b / a",
                                "Product of roots: c / a",
                                "Vertex form: a(x - h)^2 + k = 0, where (h, k) is the vertex"
                            ],
                            "worked_examples": [
                                {
                                    "question": "Solve x^2 - 5x + 6 = 0 by factorisation.",
                                    "steps": [
                                        "Find two numbers that multiply to 6 and add to -5. Those numbers are -2 and -3.",
                                        "Write the quadratic as (x - 2)(x - 3) = 0.",
                                        "Set each factor equal to zero: x - 2 = 0 or x - 3 = 0.",
                                        "Therefore x = 2 or x = 3."
                                    ],
                                    "answer": "x = 2 or x = 3."
                                },
                                {
                                    "question": "Solve 2x^2 + 3x - 2 = 0 using the quadratic formula.",
                                    "steps": [
                                        "Identify a = 2, b = 3, c = -2.",
                                        "Compute the discriminant: Δ = 3^2 - 4(2)(-2) = 9 + 16 = 25.",
                                        "Apply the formula: x = (-3 ± √25) / 4 = (-3 ± 5) / 4.",
                                        "So x = 2/4 = 1/2 or x = -8/4 = -2."
                                    ],
                                    "answer": "x = 1/2 or x = -2."
                                },
                                {
                                    "question": "Use completing the square to solve x^2 - 6x + 5 = 0.",
                                    "steps": [
                                        "Move the constant: x^2 - 6x = -5.",
                                        "Add (6/2)^2 = 9 to both sides: x^2 - 6x + 9 = 4.",
                                        "Factor the left-hand side: (x - 3)^2 = 4.",
                                        "Take square roots: x - 3 = ±2.",
                                        "So x = 5 or x = 1."
                                    ],
                                    "answer": "x = 1 or x = 5."
                                }
                            ],
                            "exam_tips": [
                                "Always put the equation in standard form before identifying a, b, and c.",
                                "Check the discriminant first: it tells you how many real roots to expect and whether the equation is likely to factor nicely.",
                                "When factorising, check the signs carefully; the product and sum must match the coefficients.",
                                "If you use the quadratic formula, write each coefficient clearly to avoid sign mistakes."
                            ],
                            "common_mistakes": [
                                "Using b^2 + 4ac instead of b^2 - 4ac in the discriminant.",
                                "Forgetting that a ≠ 0 and that the standard form must be used before extracting a, b, and c.",
                                "Stopping after finding one root when the equation has two solutions or a repeated root.",
                                "Ignoring a negative sign when moving terms across the equation."
                            ],
                            "flashcards": [
                                {"front": "What is the standard form of a quadratic equation?", "back": "ax^2 + bx + c = 0, where a ≠ 0."},
                                {"front": "What does the discriminant tell you?", "back": "It tells you the number and type of real roots: Δ > 0 gives two real roots, Δ = 0 gives one repeated real root, and Δ < 0 gives no real roots."},
                                {"front": "When is factorisation most useful?", "back": "When the quadratic splits cleanly into two linear factors with integer or simple rational values."},
                                {"front": "When do you use the quadratic formula?", "back": "When factorisation is not straightforward or when you need a reliable method for any quadratic."}
                            ],
                            "practice_questions": [
                                {
                                    "question": "Solve x^2 - 9 = 0.",
                                    "options": ["x = 3 only", "x = -3 only", "x = 3 or x = -3", "x = 9"],
                                    "correct_answer": "C",
                                    "answer": "x = 3 or x = -3.",
                                    "explanation": "Factorise as (x - 3)(x + 3) = 0, then set each bracket to zero."
                                },
                                {
                                    "question": "Solve x^2 - 4x + 4 = 0.",
                                    "options": ["x = 2 only", "x = -2 only", "x = 4 or x = -4", "x = 1 or x = 4"],
                                    "correct_answer": "A",
                                    "answer": "x = 2 only.",
                                    "explanation": "This is a perfect square: (x - 2)^2 = 0, so the repeated root is x = 2."
                                },
                                {
                                    "question": "Find the discriminant of x^2 - 7x + 10 = 0 and state the nature of the roots.",
                                    "options": ["Δ = 9; two distinct real roots", "Δ = -9; no real roots", "Δ = 0; one repeated root", "Δ = 49; one repeated root"],
                                    "correct_answer": "A",
                                    "answer": "Δ = (-7)^2 - 4(1)(10) = 49 - 40 = 9; there are two distinct real roots.",
                                    "explanation": "Since Δ > 0, there are two different real roots."
                                },
                                {
                                    "question": "Solve 3x^2 + 5x - 2 = 0 correct to 3 significant figures.",
                                    "options": ["x = 0.333 or x = -2", "x = 0.5 or x = -2/3", "x = 0.333 or x = -2.00", "x = 0.5 or x = -2"],
                                    "correct_answer": "D",
                                    "answer": "x = 0.5 or x = -2/3 (approximately -0.667).",
                                    "explanation": "Use the quadratic formula with a = 3, b = 5, c = -2 to obtain x = (-5 ± √49) / 6 = (-5 ± 7) / 6, giving x = 1/3 or x = -2. If the question expects fractions, the exact solutions are x = 1/3 and x = -2; if the question expects decimals, x ≈ 0.333 and x = -2."
                                }
                            ],
                            "resources": [
                                {
                                    "type": "summary",
                                    "title": "Quadratic Equations summary",
                                    "content": "Factorise or use the formula. Quadratic equations take the form ax^2 + bx + c = 0. Use factorisation when possible, otherwise use the quadratic formula. The discriminant Δ = b^2 - 4ac decides whether there are two, one, or no real roots, and the graph is a parabola."
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}


KNOWN_SAMPLE_LIBRARY_PLACEHOLDER_SLUGS = {
    "library_qualifications": {"cambridge-igcse"},
    "library_subjects": {"international-mathematics-0607-extended"},
    "library_topics": {"quadratic-equations"},
}


def _library_record_is_known_sample_placeholder(table_name: str, record: Any) -> bool:
    if not isinstance(record, dict):
        return False

    slug = str(record.get("slug") or record.get("id") or "").strip().lower()
    title = str(record.get("title") or record.get("name") or "").strip().lower()

    if table_name in KNOWN_SAMPLE_LIBRARY_PLACEHOLDER_SLUGS and slug in KNOWN_SAMPLE_LIBRARY_PLACEHOLDER_SLUGS[table_name]:
        return True

    if table_name == "library_resources":
        if slug.startswith("quadratic-equations"):
            return True
        if "quadratic" in title and "equation" in title:
            return True

    if "sample catalog entry" in title or "sample" in title and "catalog" in title:
        return True

    return False


def _db_update(db: Any, table_name: str, query: Dict[str, Any], update_payload: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(db, table_name):
        collection = getattr(db, table_name)
        if hasattr(collection, "update_one"):
            result = _call_db_action(collection.update_one, query, {"$set": update_payload})
            return result if isinstance(result, dict) else {"matched_count": 0, "modified_count": 0}

    rows = getattr(db, "rows", None)
    if isinstance(rows, dict):
        table_rows = rows.setdefault(table_name, [])
        matched = 0
        for row in table_rows:
            if all(row.get(k) == v for k, v in query.items()):
                row.update(update_payload)
                matched += 1
        return {"matched_count": matched, "modified_count": matched}

    raise RuntimeError("Library catalog database is not configured for updates.")




def normalize_record(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if record is None:
        return None
    normalized = dict(record)
    if "id" not in normalized and "_id" in normalized:
        normalized["id"] = normalized["_id"]
    if "_id" not in normalized and "id" in normalized:
        normalized["_id"] = normalized["id"]
    return normalized


def normalize_supabase_id(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if record is None:
        return None
    normalized = normalize_record(record)
    if normalized is None:
        return None
    if "id" not in normalized and "_id" in normalized:
        normalized["id"] = normalized["_id"]
    normalized.pop("_id", None)
    return normalized


def ensure_response_id(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    normalized = normalize_supabase_id(record)
    if normalized is None:
        return None
    if "id" not in normalized and "_id" in normalized:
        normalized["id"] = normalized["_id"]
    normalized.pop("_id", None)
    if "id" not in normalized:
        normalized["id"] = str(uuid.uuid4())
    return normalized


def strip_markdown_fences(text: Optional[str]) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def validate_quiz_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Quiz response must be a JSON object.")

    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("Quiz response must include a non-empty 'questions' array.")

    cleaned_questions: List[Dict[str, Any]] = []
    allowed_question_types = {"multiple_choice", "true_false", "short_answer"}

    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index} must be an object.")

        q_type = str(item.get("type", "")).strip().lower()
        if q_type not in allowed_question_types:
            raise ValueError(f"Question {index} has unsupported type '{item.get('type')}'.")

        question_text = str(item.get("question", "")).strip()
        if not question_text:
            raise ValueError(f"Question {index} is missing 'question'.")

        explanation = str(item.get("explanation", "")).strip()
        if not explanation:
            raise ValueError(f"Question {index} is missing 'explanation'.")

        if q_type == "multiple_choice":
            options = item.get("options")
            if not isinstance(options, list) or len(options) < 2:
                raise ValueError(f"Question {index} must include at least two answer options.")
            normalized_options = [str(opt).strip() for opt in options]
            normalized_options = [opt for opt in normalized_options if opt]
            if len(normalized_options) < 2:
                raise ValueError(f"Question {index} has empty or invalid answer choices.")

            correct_answer = str(item.get("correct_answer", "")).strip()
            if not correct_answer:
                raise ValueError(f"Question {index} is missing 'correct_answer'.")

            if correct_answer.upper() in {"A", "B", "C", "D"}:
                index_value = ord(correct_answer.upper()) - ord("A")
                if index_value >= len(normalized_options):
                    raise ValueError(f"Question {index} has a correct answer label that does not match the answer choices.")
            elif correct_answer not in normalized_options:
                raise ValueError(f"Question {index} has a correct answer that is not present in the options.")

            cleaned_questions.append({
                "type": "multiple_choice",
                "question": question_text,
                "options": normalized_options,
                "correct_answer": correct_answer.upper() if correct_answer.upper() in {"A", "B", "C", "D"} else correct_answer,
                "explanation": explanation,
            })
            continue

        if q_type == "true_false":
            correct_answer = str(item.get("correct_answer", "")).strip().lower()
            if correct_answer not in {"true", "false", "a", "b"}:
                raise ValueError(f"Question {index} must use 'true'/'false' or 'A'/'B' as the correct answer.")
            cleaned_questions.append({
                "type": "true_false",
                "question": question_text,
                "options": ["True", "False"],
                "correct_answer": "A" if correct_answer in {"true", "a"} else "B",
                "explanation": explanation,
            })
            continue

        answer = str(item.get("answer", item.get("correct_answer", ""))).strip()
        if not answer:
            raise ValueError(f"Question {index} is missing the answer for a short-answer question.")
        cleaned_questions.append({
            "type": "short_answer",
            "question": question_text,
            "answer": answer,
            "explanation": explanation,
        })

    return {"questions": cleaned_questions}


def _require_library_seed_field(item: Dict[str, Any], field_name: str, path: str) -> Any:
    value = item.get(field_name)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"Library seed field '{field_name}' is required at {path}.")
    return value


def _slugify_library_name(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    candidate = re.sub(r"[^a-z0-9]+", "-", candidate)
    candidate = re.sub(r"-+", "-", candidate).strip("-")
    return candidate or "resource"


def _build_unique_resource_slug(topic_slug: str, resource_title: str, seen: Optional[set] = None) -> str:
    base = _slugify_library_name(f"{topic_slug}-{resource_title}")
    if not base:
        base = _slugify_library_name(topic_slug or "resource")
    slug = base
    index = 2
    container = seen if seen is not None else set()
    while slug in container:
        slug = f"{base}-{index}"
        index += 1
    if seen is not None:
        container.add(slug)
    return slug


def _coerce_library_payload(resource_type: str, value: Any, original: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return {resource_type: copy.deepcopy(value)}
    if value is None:
        if isinstance(original, dict):
            payload = {k: copy.deepcopy(v) for k, v in original.items() if k not in {"resource_type", "slug", "title", "status", "type"}}
            if payload:
                return payload
        return {resource_type: []}
    if isinstance(value, str):
        return {resource_type: value}
    return {resource_type: copy.deepcopy(value)}


def _convert_topic_resources_to_seed(topic: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(topic, dict):
        return []

    topic_slug = str(topic.get("slug") or topic.get("id") or "topic")
    topic_title = str(topic.get("title") or topic.get("name") or topic_slug)
    used_slugs = set()
    resources: List[Dict[str, Any]] = []
    existing_resource_types = set()

    for existing in topic.get("resources", []) or []:
        if not isinstance(existing, dict):
            continue
        resource_type = str(existing.get("resource_type") or existing.get("type") or "summary").strip().lower() or "summary"
        resource_title = str(existing.get("title") or existing.get("name") or resource_type.replace("_", " ").title())
        payload = existing.get("payload")
        if payload is None:
            payload = {}
            if "content" in existing:
                payload = {"content": copy.deepcopy(existing.get("content"))}
            else:
                payload = {k: copy.deepcopy(v) for k, v in existing.items() if k not in {"type", "resource_type", "title", "name", "status", "slug"}}
        if not isinstance(payload, dict):
            payload = {"content": copy.deepcopy(payload)}
        resource_title = str(existing.get("title") or resource_title)
        resources.append({
            "slug": _build_unique_resource_slug(topic_slug, resource_title, used_slugs),
            "resource_type": resource_type,
            "title": resource_title,
            "status": str(existing.get("status", topic.get("status", "published"))).lower(),
            "payload": payload,
        })
        existing_resource_types.add(resource_type)

    summary_payload = {
        key: copy.deepcopy(value)
        for key, value in {
            "summary": topic.get("summary"),
            "syllabus_note": topic.get("syllabus_note"),
            "description": topic.get("description"),
        }.items()
        if value is not None
    }
    if summary_payload and "summary" not in existing_resource_types:
        summary_title = f"{topic_title} Summary"
        payload = dict(summary_payload)
        if "summary" in payload and not isinstance(payload.get("summary"), dict):
            payload["content"] = payload.pop("summary")
        elif "description" in payload and "content" not in payload:
            payload["content"] = payload.pop("description")
        resources.append({
            "slug": _build_unique_resource_slug(topic_slug, summary_title, used_slugs),
            "resource_type": "summary",
            "title": summary_title,
            "status": str(topic.get("status", "published")).lower(),
            "payload": payload,
        })

    section_mapping = [
        ("notes", "notes", "Notes"),
        ("formulae", "formulae", "Formulae"),
        ("worked_examples", "worked_examples", "Worked examples"),
        ("exam_tips", "exam_tips", "Exam tips"),
        ("common_mistakes", "common_mistakes", "Common mistakes"),
        ("flashcards", "flashcards", "Flashcards"),
        ("practice_questions", "practice_questions", "Practice questions"),
    ]
    for key, resource_type, label in section_mapping:
        if resource_type in existing_resource_types:
            continue
        section_value = topic.get(key)
        if section_value is None:
            continue
        payload = _coerce_library_payload(resource_type, section_value)
        resource_title = f"{topic_title} {label}"
        resources.append({
            "slug": _build_unique_resource_slug(topic_slug, resource_title, used_slugs),
            "resource_type": resource_type,
            "title": resource_title,
            "status": str(topic.get("status", "published")).lower(),
            "payload": payload,
        })

    return resources


def convert_default_library_catalog_to_seed(catalog: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    source = copy.deepcopy(catalog if isinstance(catalog, dict) else DEFAULT_LIBRARY_CATALOG)
    if not isinstance(source, dict):
        raise ValueError("Library catalog must be an object.")

    qualifications = source.get("qualifications")
    if not isinstance(qualifications, list):
        raise ValueError("Library catalog must include a 'qualifications' list.")

    converted: List[Dict[str, Any]] = []
    for qualification_index, qualification in enumerate(qualifications):
        if not isinstance(qualification, dict):
            raise ValueError(f"Qualification at index {qualification_index} must be an object.")
        qualification_slug = str(qualification.get("slug") or qualification.get("id") or f"qualification-{qualification_index}")
        qualification_name = str(qualification.get("name") or qualification_slug)
        qualification_status = str(qualification.get("status", "published")).lower()

        subjects = qualification.get("subjects", []) or []
        converted_subjects: List[Dict[str, Any]] = []
        for subject_index, subject in enumerate(subjects):
            if not isinstance(subject, dict):
                continue
            subject_slug = str(subject.get("slug") or subject.get("id") or f"subject-{subject_index}")
            subject_name = str(subject.get("name") or subject_slug)
            subject_status = str(subject.get("status", "published")).lower()
            topics = subject.get("topics", []) or []
            converted_topics: List[Dict[str, Any]] = []
            for topic_index, topic in enumerate(topics):
                if not isinstance(topic, dict):
                    continue
                topic_slug = str(topic.get("slug") or topic.get("id") or f"topic-{topic_index}")
                topic_title = str(topic.get("title") or topic.get("name") or topic_slug)
                converted_topics.append({
                    "slug": topic_slug,
                    "title": topic_title,
                    "status": str(topic.get("status", "published")).lower(),
                    "resources": _convert_topic_resources_to_seed(topic),
                })
            converted_subjects.append({
                "slug": subject_slug,
                "name": subject_name,
                "status": subject_status,
                "topics": converted_topics,
            })
        converted.append({
            "slug": qualification_slug,
            "name": qualification_name,
            "status": qualification_status,
            "subjects": converted_subjects,
        })

    return {"qualifications": converted}


def validate_library_seed(seed: Any) -> Dict[str, Any]:
    if not isinstance(seed, dict):
        raise ValueError("Library seed must be an object.")

    qualifications = seed.get("qualifications")
    if not isinstance(qualifications, list) or not qualifications:
        raise ValueError("Library seed must include a non-empty 'qualifications' list.")
    normalized_qualifications: List[Dict[str, Any]] = []
    for qualification_index, qualification in enumerate(qualifications):
        if not isinstance(qualification, dict):
            raise ValueError(f"Qualification at index {qualification_index} must be an object.")
        qualification_path = f"qualifications[{qualification_index}]"
        qualification_slug = _require_library_seed_field(qualification, "slug", qualification_path)
        name = _require_library_seed_field(qualification, "name", qualification_path)
        status = str(qualification.get("status", "published")).lower()

        subjects = qualification.get("subjects", [])
        if subjects is None:
            subjects = []
        if not isinstance(subjects, list):
            raise ValueError(f"Qualification '{qualification_slug}' must include a 'subjects' list.")

        normalized_subjects: List[Dict[str, Any]] = []
        for subject_index, subject in enumerate(subjects):
            if not isinstance(subject, dict):
                raise ValueError(f"Subject at '{qualification_path}.subjects[{subject_index}]' must be an object.")
            subject_path = f"{qualification_path}.subjects[{subject_index}]"
            subject_slug = _require_library_seed_field(subject, "slug", subject_path)
            subject_name = _require_library_seed_field(subject, "name", subject_path)
            subject_status = str(subject.get("status", "published")).lower()

            topics = subject.get("topics", [])
            if topics is None:
                topics = []
            if not isinstance(topics, list):
                raise ValueError(f"Subject '{subject_slug}' must include a 'topics' list.")

            normalized_topics: List[Dict[str, Any]] = []
            for topic_index, topic in enumerate(topics):
                if not isinstance(topic, dict):
                    raise ValueError(f"Topic at '{subject_path}.topics[{topic_index}]' must be an object.")
                topic_path = f"{subject_path}.topics[{topic_index}]"
                topic_slug = _require_library_seed_field(topic, "slug", topic_path)
                title = _require_library_seed_field(topic, "title", topic_path)
                topic_status = str(topic.get("status", "published")).lower()

                resources = topic.get("resources", [])
                if resources is None:
                    resources = []
                if not isinstance(resources, list):
                    raise ValueError(f"Topic '{topic_slug}' must include a 'resources' list.")

                normalized_resources: List[Dict[str, Any]] = []
                used_slugs = set()
                for resource_index, resource in enumerate(resources):
                    if not isinstance(resource, dict):
                        raise ValueError(f"Resource at '{topic_path}.resources[{resource_index}]' must be an object.")
                    resource_path = f"{topic_path}.resources[{resource_index}]"
                    resource_slug = str(resource.get("slug") or _build_unique_resource_slug(str(topic_slug), str(resource.get("title") or f"resource-{resource_index}"), used_slugs)).strip()
                    resource_type = _require_library_seed_field(resource, "resource_type", resource_path)
                    resource_title = _require_library_seed_field(resource, "title", resource_path)
                    resource_status = str(resource.get("status", "published")).lower()
                    payload = resource.get("payload")
                    if payload is None or not isinstance(payload, dict):
                        raise ValueError(f"Resource '{resource_title}' at {resource_path} must include a dictionary 'payload'.")
                    normalized_resources.append({
                        "slug": resource_slug,
                        "resource_type": str(resource_type),
                        "title": str(resource_title),
                        "status": resource_status,
                        "payload": payload,
                    })

                normalized_topics.append({
                    "slug": str(topic_slug),
                    "title": str(title),
                    "status": topic_status,
                    "resources": normalized_resources,
                })

            normalized_subjects.append({
                "slug": str(subject_slug),
                "name": str(subject_name),
                "status": subject_status,
                "topics": normalized_topics,
            })

        normalized_qualifications.append({
            "slug": str(qualification_slug),
            "name": str(name),
            "status": status,
            "subjects": normalized_subjects,
        })

    return {"qualifications": normalized_qualifications}


def _call_db_action(func, *args, **kwargs):
    result = func(*args, **kwargs)
    if hasattr(result, "__await__"):
        try:
            import asyncio
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(result)

        import threading

        captured = {}

        def runner():
            local_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(local_loop)
                captured["value"] = local_loop.run_until_complete(result)
            finally:
                local_loop.close()
                asyncio.set_event_loop(None)

        thread = threading.Thread(target=runner)
        thread.start()
        thread.join()
        return captured.get("value")
    return result


def _unwrap_db_rows(result: Any) -> List[Dict[str, Any]]:
    if result is None:
        return []
    if hasattr(result, "data"):
        payload = result.data
    elif isinstance(result, dict) and "data" in result:
        payload = result["data"]
    else:
        payload = result

    if isinstance(payload, list):
        return [dict(item) if isinstance(item, dict) else item for item in payload]
    if isinstance(payload, dict):
        return [dict(payload)]
    return []


def _unwrap_db_record(result: Any) -> Optional[Dict[str, Any]]:
    rows = _unwrap_db_rows(result)
    return rows[0] if rows else None


def _db_has_library_catalog(db: Any) -> bool:
    if db is None:
        return False
    if hasattr(db, "library_qualifications") and hasattr(db, "library_subjects") and hasattr(db, "library_topics") and hasattr(db, "library_resources"):
        return True
    rows = getattr(db, "rows", None)
    if isinstance(rows, dict):
        return all(table_name in rows for table_name in ["library_qualifications", "library_subjects", "library_topics", "library_resources"])
    return False


def _db_table_rows(db: Any, table_name: str):
    if hasattr(db, table_name):
        collection = getattr(db, table_name)
        if hasattr(collection, "find"):
            rows = _call_db_action(collection.find({}).to_list, 1000)
            normalized_rows = _unwrap_db_rows(rows)
            return normalized_rows if normalized_rows else []
        if hasattr(collection, "select"):
            result = _call_db_action(collection.select, "*")
            normalized_rows = _unwrap_db_rows(result)
            return normalized_rows if normalized_rows else []
    rows = getattr(db, "rows", None)
    if isinstance(rows, dict):
        return list(rows.get(table_name, []))
    return []


def _db_table_exists(db: Any, table_name: str) -> bool:
    if hasattr(db, table_name):
        return True
    rows = getattr(db, "rows", None)
    return isinstance(rows, dict) and table_name in rows


def _db_insert(db: Any, table_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(db, table_name):
        collection = getattr(db, table_name)
        if hasattr(collection, "insert_one"):
            inserted = _call_db_action(collection.insert_one, item)
            normalized = _unwrap_db_record(inserted)
            return normalized if isinstance(normalized, dict) else dict(item)
    if hasattr(db, "insert_one"):
        inserted = _call_db_action(db.insert_one, {**item, "_table": table_name})
        normalized = _unwrap_db_record(inserted)
        return normalized if isinstance(normalized, dict) else {**item, "_table": table_name}
    rows = getattr(db, "rows", None)
    if isinstance(rows, dict):
        row_payload = dict(item)
        row_payload["_table"] = table_name
        rows.setdefault(table_name, []).append(row_payload)
        return row_payload
    raise RuntimeError("Library catalog database is not configured.")


def _db_find_one(db: Any, table_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if hasattr(db, table_name):
        collection = getattr(db, table_name)
        if hasattr(collection, "find_one"):
            found = _call_db_action(collection.find_one, query)
            normalized = _unwrap_db_record(found)
            return normalized if isinstance(normalized, dict) else None
    rows = getattr(db, "rows", None)
    if isinstance(rows, dict):
        for record in rows.get(table_name, []):
            if all(record.get(k) == v for k, v in query.items()):
                return dict(record)
    return None


def import_library_seed(seed: Any, db: Optional[Any] = None, report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    validated = validate_library_seed(seed)
    active_db = db if db is not None else globals().get("db")
    if active_db is None or not _db_has_library_catalog(active_db):
        raise RuntimeError("Library catalog database is not configured.")

    counters = report if isinstance(report, dict) else {
        "created": {"library_qualifications": 0, "library_subjects": 0, "library_topics": 0, "library_resources": 0},
        "skipped": {"library_qualifications": 0, "library_subjects": 0, "library_topics": 0, "library_resources": 0},
        "failed": {"library_qualifications": 0, "library_subjects": 0, "library_topics": 0, "library_resources": 0},
        "errors": [],
    }
    imported = {"qualifications": []}

    for qualification in validated["qualifications"]:
        qualification_key = {"slug": qualification["slug"]}
        try:
            existing_qualification = _db_find_one(active_db, "library_qualifications", qualification_key)
            if existing_qualification is None:
                qual_doc = {"slug": qualification["slug"], "name": qualification["name"], "status": qualification.get("status", "published")}
                _db_insert(active_db, "library_qualifications", qual_doc)
                counters["created"]["library_qualifications"] += 1
            elif _library_record_is_known_sample_placeholder("library_qualifications", existing_qualification):
                _db_update(active_db, "library_qualifications", qualification_key, {
                    "name": qualification["name"],
                    "status": qualification.get("status", "published"),
                })
                counters["skipped"]["library_qualifications"] += 1
            else:
                counters["skipped"]["library_qualifications"] += 1
        except Exception as exc:
            counters["failed"]["library_qualifications"] += 1
            counters["errors"].append({"table": "library_qualifications", "slug": qualification["slug"], "error": str(exc)})

        for subject in qualification["subjects"]:
            subject_key = {"slug": subject["slug"], "qualification_slug": qualification["slug"]}
            try:
                existing_subject = _db_find_one(active_db, "library_subjects", subject_key)
                if existing_subject is None:
                    _db_insert(active_db, "library_subjects", {
                        "slug": subject["slug"],
                        "qualification_slug": qualification["slug"],
                        "name": subject["name"],
                        "status": subject.get("status", "published"),
                    })
                    counters["created"]["library_subjects"] += 1
                elif _library_record_is_known_sample_placeholder("library_subjects", existing_subject):
                    _db_update(active_db, "library_subjects", subject_key, {
                        "name": subject["name"],
                        "status": subject.get("status", "published"),
                    })
                    counters["skipped"]["library_subjects"] += 1
                else:
                    counters["skipped"]["library_subjects"] += 1
            except Exception as exc:
                counters["failed"]["library_subjects"] += 1
                counters["errors"].append({"table": "library_subjects", "slug": subject["slug"], "error": str(exc)})

            for topic in subject["topics"]:
                topic_key = {"slug": topic["slug"], "subject_slug": subject["slug"]}
                try:
                    existing_topic = _db_find_one(active_db, "library_topics", topic_key)
                    if existing_topic is None:
                        _db_insert(active_db, "library_topics", {
                            "slug": topic["slug"],
                            "subject_slug": subject["slug"],
                            "title": topic["title"],
                            "status": topic.get("status", "published"),
                        })
                        counters["created"]["library_topics"] += 1
                    elif _library_record_is_known_sample_placeholder("library_topics", existing_topic):
                        _db_update(active_db, "library_topics", topic_key, {
                            "title": topic["title"],
                            "status": topic.get("status", "published"),
                        })
                        counters["skipped"]["library_topics"] += 1
                    else:
                        counters["skipped"]["library_topics"] += 1
                except Exception as exc:
                    counters["failed"]["library_topics"] += 1
                    counters["errors"].append({"table": "library_topics", "slug": topic["slug"], "error": str(exc)})

                for resource in topic["resources"]:
                    resource_key = {"slug": resource.get("slug") or resource.get("title", topic["slug"]), "topic_slug": topic["slug"]}
                    try:
                        existing_resource = _db_find_one(active_db, "library_resources", resource_key)
                        if existing_resource is None:
                            _db_insert(active_db, "library_resources", {
                                "slug": resource.get("slug") or resource.get("title", topic["slug"]),
                                "topic_slug": topic["slug"],
                                "resource_type": resource["resource_type"],
                                "title": resource["title"],
                                "status": resource.get("status", "published"),
                                "payload": resource["payload"],
                            })
                            counters["created"]["library_resources"] += 1
                        elif _library_record_is_known_sample_placeholder("library_resources", existing_resource):
                            _db_update(active_db, "library_resources", resource_key, {
                                "resource_type": resource["resource_type"],
                                "title": resource["title"],
                                "status": resource.get("status", "published"),
                                "payload": resource["payload"],
                            })
                            counters["skipped"]["library_resources"] += 1
                        else:
                            counters["skipped"]["library_resources"] += 1
                    except Exception as exc:
                        counters["failed"]["library_resources"] += 1
                        counters["errors"].append({"table": "library_resources", "slug": resource.get("slug") or resource.get("title", topic["slug"]), "error": str(exc)})
        imported["qualifications"].append(qualification)

    if report is None:
        return imported
    return counters


def import_default_library_catalog(seed: Optional[Any] = None, db: Optional[Any] = None) -> Dict[str, Any]:
    catalog_seed = convert_default_library_catalog_to_seed(seed if isinstance(seed, dict) else DEFAULT_LIBRARY_CATALOG)
    report = {
        "created": {"library_qualifications": 0, "library_subjects": 0, "library_topics": 0, "library_resources": 0},
        "skipped": {"library_qualifications": 0, "library_subjects": 0, "library_topics": 0, "library_resources": 0},
        "failed": {"library_qualifications": 0, "library_subjects": 0, "library_topics": 0, "library_resources": 0},
        "errors": [],
        "status": "ok",
    }
    import_library_seed(catalog_seed, db=db, report=report)
    if any(report["failed"].values()):
        report["status"] = "partial_failure"
    return report


def get_published_library_catalog(db: Optional[Any] = None) -> Dict[str, Any]:
    active_db = db if db is not None else globals().get("db")
    default_db = globals().get("db")
    is_default_local_db = (not HAS_REAL_SUPABASE) and (active_db is default_db)
    memory_catalog = MEMORY_STORE.get("library_catalog")

    if isinstance(memory_catalog, dict) and ALLOW_LOCAL_LIBRARY_FALLBACK and is_default_local_db:
        filtered = _filter_published_library_item(memory_catalog)
        if isinstance(filtered, dict):
            return {"qualifications": filtered.get("qualifications", [])}

    if active_db is None:
        if not ALLOW_LOCAL_LIBRARY_FALLBACK:
            raise RuntimeError("Library catalog database is not configured and local fallback is disabled. Set ALLOW_LOCAL_LIBRARY_FALLBACK=1 only for explicit local development.")
        default_catalog = _filter_published_library_item(DEFAULT_LIBRARY_CATALOG)
        if isinstance(default_catalog, dict):
            return {"qualifications": default_catalog.get("qualifications", [])}
        return {"qualifications": []}

    if not HAS_REAL_SUPABASE and is_default_local_db:
        if not ALLOW_LOCAL_LIBRARY_FALLBACK:
            raise RuntimeError("Library catalog database is not configured and local fallback is disabled. Set ALLOW_LOCAL_LIBRARY_FALLBACK=1 only for explicit local development.")
        if isinstance(memory_catalog, dict):
            filtered = _filter_published_library_item(memory_catalog)
            if isinstance(filtered, dict):
                return {"qualifications": filtered.get("qualifications", [])}
        default_catalog = _filter_published_library_item(DEFAULT_LIBRARY_CATALOG)
        if isinstance(default_catalog, dict):
            return {"qualifications": default_catalog.get("qualifications", [])}
        return {"qualifications": []}

    if not _db_has_library_catalog(active_db):
        raise RuntimeError("Library catalog database is not configured.")

    try:
        qualifications = []
        for row in _db_table_rows(active_db, "library_qualifications"):
            row = dict(row)
            slug = str(row.get("slug") or row.get("id") or "")
            if not slug:
                continue
            subject_rows = []
            for subject_row in _db_table_rows(active_db, "library_subjects"):
                subject_record = dict(subject_row)
                if str(subject_record.get("qualification_slug") or subject_record.get("qualification_id")) == slug:
                    subject_slug = str(subject_record.get("slug") or subject_record.get("id") or "")
                    if not subject_slug:
                        continue
                    topics = []
                    for topic_row in _db_table_rows(active_db, "library_topics"):
                        topic_record = dict(topic_row)
                        if str(topic_record.get("subject_slug") or topic_record.get("subject_id")) == subject_slug:
                            resource_rows = []
                            for resource_row in _db_table_rows(active_db, "library_resources"):
                                resource_record = dict(resource_row)
                                if str(resource_record.get("topic_slug") or resource_record.get("topic_id")) == str(topic_record.get("slug") or topic_record.get("id") or ""):
                                    resource_rows.append({
                                        "resource_type": resource_record.get("resource_type", "notes"),
                                        "title": resource_record.get("title", "Untitled"),
                                        "status": resource_record.get("status", "published"),
                                        "payload": resource_record.get("payload", {}),
                                    })
                            topics.append({
                                "slug": str(topic_record.get("slug") or topic_record.get("id") or ""),
                                "title": topic_record.get("title", "Untitled"),
                                "status": topic_record.get("status", "published"),
                                "resources": resource_rows,
                            })
                    subject_rows.append({
                        "slug": subject_slug,
                        "name": subject_record.get("name", subject_slug),
                        "status": subject_record.get("status", "published"),
                        "topics": topics,
                    })
            qualifications.append({
                "slug": slug,
                "name": row.get("name", slug),
                "status": row.get("status", "published"),
                "subjects": subject_rows,
            })
    except Exception as exc:
        raise RuntimeError(f"Library catalog database query failed: {exc}") from exc

    if qualifications:
        catalog = {"qualifications": qualifications}
        filtered = _filter_published_library_item(catalog)
        return filtered if isinstance(filtered, dict) else {"qualifications": []}

    return {"qualifications": []}


def _get_published_library_catalog() -> Dict[str, Any]:
    return get_published_library_catalog()


def _filter_published_library_item(item: Any) -> Any:
    if isinstance(item, list):
        cleaned = []
        for child in item:
            filtered = _filter_published_library_item(child)
            if filtered is not None:
                cleaned.append(filtered)
        return cleaned

    if isinstance(item, dict):
        if "status" in item and str(item.get("status", "published")).lower() != "published":
            return None

        filtered = {}
        for key, value in item.items():
            if key == "status" and value is None:
                continue

            if isinstance(value, list):
                nested = _filter_published_library_item(value)
                if nested:
                    filtered[key] = nested
            elif isinstance(value, dict):
                nested = _filter_published_library_item(value)
                if nested is not None:
                    filtered[key] = nested
            else:
                filtered[key] = value
        return filtered

    return item


def _find_library_qualification(qualifications: List[Dict[str, Any]], slug: str) -> Optional[Dict[str, Any]]:
    if not isinstance(qualifications, list):
        return None
    return next((item for item in qualifications if str(item.get("slug")) == str(slug)), None)


class MemoryResult:
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None, count: Optional[int] = None):
        self.data = data or []
        self.count = count


class OperationResult:
    def __init__(self, matched_count: int = 0, modified_count: int = 0, deleted_count: int = 0):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.deleted_count = deleted_count


class MemoryTable:
    def __init__(self, name: str):
        self.name = name

    def select(self, *fields, **kwargs):
        return MemoryQueryBuilder(self.name, fields=fields, count=kwargs.get("count"))

    def insert(self, document: Dict[str, Any]):
        return MemoryQueryBuilder(self.name).insert(document)

    def update(self, payload: Dict[str, Any]):
        return MemoryQueryBuilder(self.name).update(payload)

    def delete(self):
        return MemoryQueryBuilder(self.name).delete()


class MemoryQueryBuilder:
    def __init__(self, table_name: str, fields: Optional[tuple] = None, count: Optional[str] = None):
        self.table_name = table_name
        self.fields = fields or ("*",)
        self.count = count
        self.filters = []
        self.sort_spec = None
        self.limit_value = None
        self.payload = None
        self.action = "read"

    def eq(self, field: str, value: Any):
        self.filters.append(
            lambda row, f=field, v=value: (row.get(f) if row.get(f) is not None else row.get("id" if f == "_id" else "_id")) == v
        )
        return self

    def in_(self, field: str, values: List[Any]):
        self.filters.append(
            lambda row, f=field, v=set(values): (row.get(f) if row.get(f) is not None else row.get("id" if f == "_id" else "_id")) in v
        )
        return self

    def order(self, field: str, desc: bool = False):
        self.sort_spec = (field, desc)
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def insert(self, document: Dict[str, Any]):
        self.action = "insert"
        self.payload = dict(document)
        return self

    def update(self, payload: Dict[str, Any]):
        self.action = "update"
        self.payload = payload
        return self

    def delete(self):
        self.action = "delete"
        return self

    def execute(self):
        rows = MEMORY_STORE.setdefault(self.table_name, [])
        if self.action == "insert":
            payload = dict(self.payload or {})
            if "id" not in payload and "_id" not in payload:
                payload["id"] = str(uuid.uuid4())
            rows.append(dict(payload))
            return MemoryResult(data=[dict(payload)])

        filtered: List[Dict[str, Any]] = []
        for row in rows:
            record = normalize_record(dict(row))
            if record is not None and all(f(record) for f in self.filters):
                filtered.append(record)

        if self.action == "delete":
            for row in list(rows):
                record = normalize_record(dict(row))
                if record is not None and all(f(record) for f in self.filters):
                    rows.remove(row)
            return MemoryResult(data=[])

        if self.action == "update":
            updated_rows: List[Dict[str, Any]] = []
            payload = dict(self.payload or {})
            for row in rows:
                record = normalize_record(dict(row))
                if record is not None and all(f(record) for f in self.filters):
                    record.update(payload)
                    updated_rows.append(record)
                    rows[rows.index(row)] = record
            return MemoryResult(data=updated_rows)

        if self.sort_spec:
            field, desc = self.sort_spec
            filtered.sort(key=lambda row: (row.get(field) is None, str(row.get(field, ""))), reverse=desc)

        if self.limit_value is not None:
            filtered = filtered[: self.limit_value]

        if self.count == "exact":
            return MemoryResult(data=filtered, count=len(filtered))

        if self.fields and self.fields != ("*",):
            projected = []
            for row in filtered:
                item = {}
                for field in self.fields:
                    if field == "id":
                        item["id"] = row.get("id", row.get("_id"))
                    elif field == "*":
                        item = dict(row)
                    else:
                        item[field] = row.get(field)
                projected.append(item)
            return MemoryResult(data=projected)

        return MemoryResult(data=filtered)


class MemorySupabaseClient:
    def table(self, name: str):
        return MemoryTable(name)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

supabase: Any = None
if create_client is not None and SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    logger.warning("Supabase client unavailable or credentials not configured; falling back to local in-memory storage for development.")
    supabase = MemorySupabaseClient()


class SupabaseQuery:
    def __init__(self, collection_name: str, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None):
        self.collection_name = collection_name
        self.query = query or {}
        self.projection = projection or {}
        self._sort_spec = None
        self._limit_value = None

    def sort(self, *args):
        if len(args) == 1 and isinstance(args[0], list):
            self._sort_spec = args[0]
        elif len(args) == 2:
            self._sort_spec = [(args[0], -1 if args[1] < 0 else 1)]
        else:
            self._sort_spec = None
        return self

    def limit(self, count: int):
        self._limit_value = count
        return self

    @staticmethod
    def _normalize_key(key: str) -> str:
        return "id" if key in ("_id", "id") else key

    @staticmethod
    def _normalize_filter(query: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for key, value in (query or {}).items():
            normalized[SupabaseQuery._normalize_key(key)] = value
        return normalized

    @staticmethod
    def _apply_projection(document: Dict[str, Any], projection: Dict[str, Any]) -> Dict[str, Any]:
        if not document or not isinstance(projection, dict):
            return document
        projected = dict(document)
        for key, value in projection.items():
            if value == 0:
                projected.pop(key, None)
                projected.pop(key.replace("_id", "id"), None)
        return projected

    @staticmethod
    def _build_table(name: str):
        return supabase.table(name)

    async def _execute(self):
        table = self._build_table(self.collection_name).select("*")
        for field, value in self._normalize_filter(self.query).items():
            if isinstance(value, dict):
                continue
            if isinstance(value, (list, tuple, set)):
                table = table.in_(field, list(value))
            else:
                table = table.eq(field, value)

        if self._sort_spec:
            for field, direction in self._sort_spec:
                table = table.order(field, desc=(direction < 0))

        if self._limit_value is not None:
            table = table.limit(self._limit_value)

        result = table.execute()
        rows = result.data or []
        return [self._apply_projection(row, self.projection) for row in rows]

    async def to_list(self, fallback_limit: Optional[int] = None):
        if fallback_limit is not None and self._limit_value is None:
            self._limit_value = fallback_limit
        return await self._execute()


class SupabaseCollection:
    def __init__(self, name: str):
        self.name = name

    def find(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None):
        return SupabaseQuery(self.name, query=query, projection=projection)

    async def find_one(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None, sort=None):
        q = SupabaseQuery(self.name, query=query, projection=projection)
        if sort is not None:
            q.sort(sort)
        rows = await q.to_list(1)
        return rows[0] if rows else None

    async def insert_one(self, document: Dict[str, Any]):
        table = SupabaseQuery._build_table(self.name)
        payload = normalize_supabase_id(document) or dict(document)
        payload.pop("_id", None)
        result = table.insert(payload).execute()
        data = result.data or []
        return data[0] if data else None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        update_payload = update.get("$set", update) if isinstance(update, dict) and "$set" in update else update
        table = SupabaseQuery._build_table(self.name).update(update_payload)
        for field, value in SupabaseQuery._normalize_filter(query).items():
            table = table.eq(field, value)
        result = table.execute()
        rows = result.data or []
        return OperationResult(matched_count=1 if rows else 0, modified_count=1 if rows else 0)

    async def delete_one(self, query: Dict[str, Any]):
        table = SupabaseQuery._build_table(self.name).delete()
        for field, value in SupabaseQuery._normalize_filter(query).items():
            table = table.eq(field, value)
        result = table.execute()
        rows = result.data or []
        return OperationResult(deleted_count=1 if rows else 0)

    async def count_documents(self, query: Optional[Dict[str, Any]] = None):
        result = SupabaseQuery._build_table(self.name).select("id", count="exact")
        for field, value in SupabaseQuery._normalize_filter(query or {}).items():
            if isinstance(value, (list, tuple, set)):
                result = result.in_(field, list(value))
            else:
                result = result.eq(field, value)
        data = result.execute()
        if hasattr(data, "count") and data.count is not None:
            return data.count
        return len(data.data or [])

    async def create_index(self, field: str, unique: bool = False):
        return None


class SupabaseDatabase:
    users = SupabaseCollection("users")
    documents = SupabaseCollection("documents")
    summaries = SupabaseCollection("summaries")
    quizzes = SupabaseCollection("quizzes")
    question_sets = SupabaseCollection("question_sets")
    question_set_questions = SupabaseCollection("question_set_questions")
    flashcard_sets = SupabaseCollection("flashcard_sets")
    study_plans = SupabaseCollection("study_plans")
    streaks = SupabaseCollection("streaks")
    notes = SupabaseCollection("notes")
    library_qualifications = SupabaseCollection("library_qualifications")
    library_subjects = SupabaseCollection("library_subjects")
    library_topics = SupabaseCollection("library_topics")
    library_resources = SupabaseCollection("library_resources")


db = SupabaseDatabase()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Storage setup (local filesystem)
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", str(ROOT_DIR / "storage")))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
APP_NAME = "ai-study-assistant"

# AI provider configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")

if OPENROUTER_API_KEY:
    OPENAI_API_KEY = OPENROUTER_API_KEY
    OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "openrouter/free")
elif OPENAI_BASE_URL:
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", os.environ.get("OLLAMA_MODEL", "gemma4:12b"))
else:
    OPENAI_API_KEY = OPENAI_API_KEY or "ollama"
    OPENAI_BASE_URL = "http://localhost:11434/v1"
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", os.environ.get("OLLAMA_MODEL", "gemma4:12b"))

openai_client = AsyncOpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
)

# Cookie security configuration: set COOKIE_SECURE=1 in production to force Secure cookies
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0").lower() in ("1", "true", "yes")
COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Save file to local filesystem storage."""
    full_path = STORAGE_DIR / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(data)
    return {"path": path, "size": len(data), "content_type": content_type}


def get_object(path: str) -> tuple:
    """Read file from local filesystem storage."""
    full_path = STORAGE_DIR / path
    if not full_path.exists():
        raise FileNotFoundError(f"Object not found: {path}")
    return full_path.read_bytes(), "application/octet-stream"


async def llm_generate(system: str, prompt: str, model: Optional[str] = None) -> str:
    """Generate a complete LLM response (non-streaming)."""
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running or not configured.",
        )

    english_system = (
        "You are a clear, helpful study assistant. Always answer in standard English only. "
        "Keep your response concise, well-structured, and easy for students to understand."
    )

    try:
        resp = await openai_client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[
                {"role": "system", "content": english_system + " " + system},
                {"role": "user", "content": prompt},
            ],
        )
    except (TimeoutError, ConnectionError) as exc:
        logger.exception("AI completion timed out or failed to connect")
        raise HTTPException(status_code=503, detail="The AI model is temporarily unavailable. Please try again later.") from exc
    except Exception as exc:
        logger.exception("AI completion request failed")
        raise HTTPException(status_code=503, detail="The AI model request failed. Please try again later.") from exc

    content = resp.choices[0].message.content if getattr(resp, "choices", None) else ""
    cleaned = (content or "").strip()
    if not cleaned:
        raise HTTPException(status_code=502, detail="The AI model returned an empty response.")
    return cleaned


async def llm_stream(system: str, prompt: str, model: Optional[str] = None):
    """Stream LLM response as async iterator of text chunks."""
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running or not configured.",
        )

    english_system = (
        "You are a clear, helpful study assistant. Always answer in standard English only. "
        "Keep your response concise, well-structured, and easy for students to understand."
    )

    try:
        stream = await openai_client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[
                {"role": "system", "content": english_system + " " + system},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
    except (TimeoutError, ConnectionError) as exc:
        logger.exception("AI stream timed out or failed to connect")
        yield f"data: {json.dumps({'error': 'The AI model is temporarily unavailable. Please try again later.'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        return
    except Exception as exc:
        logger.exception("AI stream request failed")
        yield f"data: {json.dumps({'error': 'The AI model request failed. Please try again later.'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        return

    yielded_any = False
    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yielded_any = True
                yield delta
    except Exception as exc:
        logger.exception("AI stream iteration failed")
        yield f"data: {json.dumps({'error': 'The AI model stream ended unexpectedly. Please try again.'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        return

    if not yielded_any:
        yield "I couldn’t find enough relevant information in the uploaded document to answer that question confidently."

# Auth utilities
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ.get("JWT_SECRET", "dev-secret-key")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    # Safe diagnostic: log only cookie names (never values) and request path
    try:
        cookie_names = list(request.cookies.keys())
    except Exception:
        cookie_names = []
    logger.info("Cookie names received: %s Path: %s", cookie_names, getattr(request.url, 'path', str(request.url)))

    token = request.cookies.get("access_token")

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        user = await db.users.find_one({"id": payload["sub"]})
        if not user:
            user = await db.users.find_one({"_id": payload["sub"]})

        user = normalize_record(user)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        user.pop("password_hash", None)
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OnboardingRequest(BaseModel):
    grade_level: str
    subjects: List[str]
    curriculum: str
    exam_dates: Optional[List[Dict[str, str]]] = []
    daily_study_goal: int = 60


class SummaryRequest(BaseModel):
    document_id: str
    summary_type: str = "detailed"


class TutorRequest(BaseModel):
    document_id: str
    question: str
    difficulty_mode: str = "intermediate"
    session_id: Optional[str] = None


class QuizRequest(BaseModel):
    document_ids: List[str]
    question_types: List[str]
    difficulty: str = "medium"
    num_questions: int = 10


class FlashcardRequest(BaseModel):
    document_id: str


class StudyPlanRequest(BaseModel):
    exam_dates: List[Dict[str, str]]
    daily_study_time: int


class NoteRequest(BaseModel):
    title: str
    content: str = ""
    tags: List[str] = []
    color: str = "butter"
    is_pinned: bool = False
    document_id: Optional[str] = None


class QuestionLibraryQuestionRequest(BaseModel):
    question: str
    type: str = "multiple_choice"
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    answer: Optional[str] = None
    explanation: str = ""


class QuestionLibrarySetRequest(BaseModel):
    name: str
    subject: str = ""
    topic: str = ""
    difficulty: str = "medium"
    question_type: str = "multiple_choice"
    questions: List[QuestionLibraryQuestionRequest]


def normalize_question_library_question(raw: Any) -> Dict[str, Any]:
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
    elif hasattr(raw, "dict"):
        raw = raw.dict()

    if not isinstance(raw, dict):
        raise ValueError("Each question must be an object.")

    q_type = str(raw.get("type", "multiple_choice")).strip().lower() or "multiple_choice"
    if q_type not in {"multiple_choice", "true_false", "short_answer"}:
        raise ValueError(f"Unsupported question type '{raw.get('type')}'.")

    question_text = str(raw.get("question", "")).strip()
    if not question_text:
        raise ValueError("Each question must include a non-empty 'question' value.")

    explanation = str(raw.get("explanation", "") or "").strip()

    if q_type == "multiple_choice":
        options = raw.get("options")
        if not isinstance(options, list) or len(options) < 2:
            raise ValueError("Multiple choice questions require at least 2 options.")

        cleaned_options = [str(option).strip() for option in options if str(option).strip()]
        if len(cleaned_options) < 2:
            raise ValueError("Multiple choice questions require valid answer options.")

        correct_answer = str(raw.get("correct_answer", "") or "").strip()
        if not correct_answer:
            raise ValueError("Multiple choice questions require a correct answer.")

        if correct_answer.upper() in {"A", "B", "C", "D"}:
            option_index = ord(correct_answer.upper()) - ord("A")
            if option_index >= len(cleaned_options):
                raise ValueError("The correct answer label does not match the provided options.")
            normalized_correct_answer = correct_answer.upper()
        elif correct_answer in cleaned_options:
            normalized_correct_answer = correct_answer
        else:
            raise ValueError("The correct answer must match one of the provided options.")

        return {
            "type": "multiple_choice",
            "question": question_text,
            "options": cleaned_options,
            "correct_answer": normalized_correct_answer,
            "explanation": explanation,
        }

    if q_type == "true_false":
        correct_answer = str(raw.get("correct_answer", raw.get("answer", "")) or "").strip().lower()
        if correct_answer not in {"true", "false", "a", "b"}:
            raise ValueError("True/false questions require a valid true/false answer.")
        return {
            "type": "true_false",
            "question": question_text,
            "options": ["True", "False"],
            "correct_answer": "A" if correct_answer in {"true", "a"} else "B",
            "explanation": explanation,
        }

    answer = str(raw.get("answer", raw.get("correct_answer", "")) or "").strip()
    if not answer:
        raise ValueError("Short answer questions require an answer.")
    return {
        "type": "short_answer",
        "question": question_text,
        "answer": answer,
        "explanation": explanation,
    }


# Helper: Extract text from files
def extract_text_from_file(file_content: bytes, file_type: str) -> str:
    try:
        if file_type == "application/pdf":
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""

            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            return text

        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = DocxDocument(io.BytesIO(file_content))

            return "\n".join(
                [para.text for para in doc.paragraphs]
            )

        elif file_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(io.BytesIO(file_content))
            text = ""

            for slide in prs.slides:
                for shape in slide.shapes:
                    txt = getattr(shape, "text", None)

                    if txt:
                        text += txt + "\n"

            return text

        elif file_type == "text/plain":
            return file_content.decode("utf-8")

        else:
            return ""

    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""


# Auth endpoints
@api_router.post("/auth/register")
async def register(req: RegisterRequest, response: Response):
    email = req.email.lower()

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    existing = result.data[0] if result.data else None

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user_id = str(uuid.uuid4())

    user_doc = {
        "id": user_id,
        "email": email,
        "name": req.name,
        "password_hash": hash_password(req.password),
        "onboarded": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    supabase.table("users").insert(user_doc).execute()

    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    # For local development and test runs, do not require Secure cookie flag
    # so cookies are sent over HTTP. In production, set secure=True via env.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=900,
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=604800,
        path="/"
    )

    user_doc.pop("password_hash", None)

    return user_doc


@api_router.post("/auth/login")
async def login(req: LoginRequest, response: Response):
    email = req.email.lower()

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    user = result.data[0] if result.data else None
    user = normalize_record(user) if isinstance(user, dict) else user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        req.password,
        str(user.get("password_hash", ""))
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    user_id = str(user.get("id") or user.get("_id"))

    access_token = create_access_token(
        user_id,
        email
    )

    refresh_token = create_refresh_token(user_id)

    # For local development and test runs, do not require Secure cookie flag
    # so cookies are sent over HTTP. In production, set secure=True via env.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=900,
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=604800,
        path="/"
    )

    user.pop("password_hash", None)
    user = normalize_record(user)
    return user


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/"
    )

    response.delete_cookie(
        key="refresh_token",
        path="/"
    )

    return {
        "message": "Logged out successfully"
    }


@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)

    return user


@api_router.post("/auth/onboarding")
async def complete_onboarding(
    req: OnboardingRequest,
    request: Request
):
    user = await get_current_user(request)

    update_data = {
        "school_level": req.grade_level,
        "study_preferences": {
            "subjects": req.subjects,
            "curriculum": req.curriculum,
            "exam_dates": req.exam_dates
        },
        # Keep a top-level curriculum field for compatibility
        "curriculum": req.curriculum,
        "daily_study_goal": req.daily_study_goal,
        "onboarded": True
    }

    supabase.table("users").update(
        update_data
    ).eq(
        "id",
        user["id"]
    ).execute()

    existing_streak_result = (
        supabase
        .table("streaks")
        .select("*")
        .eq("user_id", user["id"])
        .limit(1)
        .execute()
    )

    existing_streak = (
        existing_streak_result.data[0]
        if existing_streak_result.data
        else None
    )

    if not existing_streak:

        streak_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
            "total_study_minutes": 0
        }

        supabase.table(
            "streaks"
        ).insert(
            streak_doc
        ).execute()

    return {
        "message": "Onboarding completed"
    }

# File upload
@api_router.post("/documents/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    
    file_content = await file.read()
    filename = getattr(file, "filename", "") or ""
    ext = filename.split(".")[-1] if "." in filename else "bin"
    storage_path = f"{APP_NAME}/uploads/{user['id']}/{uuid.uuid4()}.{ext}"
    
    content_type = file.content_type or "application/octet-stream"
    result = put_object(storage_path, file_content, content_type)
    
    extracted_text = extract_text_from_file(file_content, content_type)
    
    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "user_id": user["id"],
        "original_filename": file.filename,
        "storage_path": result["path"],
        "content_type": content_type,
        "size": result["size"],
        "extracted_text": extracted_text,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(doc)
    
    response_doc = normalize_supabase_id(doc) or dict(doc)
    response_doc.pop("extracted_text", None)
    return response_doc

@api_router.get("/documents")
async def list_documents(request: Request):
    user = await get_current_user(request)
    docs = await db.documents.find({"user_id": user["id"], "is_deleted": False}, {"extracted_text": 0}).to_list(1000)
    normalized_docs: List[Dict[str, Any]] = []
    for d in docs:
        normalized = normalize_supabase_id(d)
        if normalized is None:
            continue
        normalized.pop("_id", None)
        normalized_docs.append(normalized)
    return normalized_docs

@api_router.get("/documents/{doc_id}/file")
async def get_document_file(doc_id: str, request: Request):
    user = await get_current_user(request)
    doc = await db.documents.find_one({
        "id": doc_id,
        "user_id": user["id"],
        "is_deleted": False
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage_path = doc.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail="Document file not found")

    try:
        file_bytes, _ = get_object(storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document file not found")

    content_type = doc.get("content_type") or "application/octet-stream"
    filename = doc.get("original_filename") or "document"

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )


@api_router.get("/documents/{doc_id}")
async def get_document(doc_id: str, request: Request):
    user = await get_current_user(request)

    doc = await db.documents.find_one({
        "id": doc_id,
        "user_id": user["id"],
        "is_deleted": False
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    response_doc = normalize_supabase_id(doc) or dict(doc)
    response_doc.pop("extracted_text", None)
    response_doc.pop("_id", None)
    return response_doc

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.documents.update_one({"_id": doc_id, "user_id": user["id"]}, {"$set": {"is_deleted": True}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted"}

# AI Summary
@api_router.post("/ai/summary")
async def generate_summary(req: SummaryRequest, request: Request):
    user = await get_current_user(request)
    doc = await db.documents.find_one({"_id": req.document_id, "user_id": user["id"], "is_deleted": False})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    existing = await db.summaries.find_one({"document_id": req.document_id, "summary_type": req.summary_type})
    if existing:
        existing = ensure_response_id(existing) or existing
        return existing
    
    text = doc.get("extracted_text", "")
    if not text:
        raise HTTPException(status_code=400, detail="No text content found in document")
    
    prompt_templates = {
        "short": (
            "Summarize the source material in 3-5 sentences using only information explicitly stated in the document. "
            "Do not invent facts, dates, examples, formulas, definitions, or names that are not present in the text. "
            "If a point is unclear or missing, say so briefly rather than guessing.\n\n"
            f"Source text:\n{text[:4000]}"
        ),
        "detailed": (
            "Create a detailed but accurate summary based only on the source material. Include: "
            "1. Main topics 2. Key concepts 3. Important definitions 4. Formulas or processes if stated 5. Exam-relevant takeaways. "
            "Do not add unsupported claims or assumptions. If important information is missing from the source, say that clearly.\n\n"
            f"Source text:\n{text[:6000]}"
        ),
        "bullet_points": (
            "Summarize the material in clear bullet points using only content explicitly present in the document. "
            "Do not infer missing facts. Group ideas logically and keep the wording precise.\n\n"
            f"Source text:\n{text[:5000]}"
        ),
        "timeline": (
            "If the source includes a sequence of events, create a timeline. Otherwise, organize the material by chronological or logical order "
            "without adding facts not present in the text.\n\n"
            f"Source text:\n{text[:5000]}"
        ),
    }

    prompt = prompt_templates.get(req.summary_type, prompt_templates["detailed"])

    summary_content = await llm_generate(
        system="You are an expert study assistant. Summarize only what is supported by the source material, and say when the document does not provide enough information.",
        prompt=prompt,
    )
    
    summary_id = str(uuid.uuid4())
    summary_doc = {
        "id": summary_id,
        "document_id": req.document_id,
        "user_id": user["id"],
        "summary_type": req.summary_type,
        "content": summary_content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.summaries.insert_one(summary_doc)
    return normalize_supabase_id(summary_doc) or dict(summary_doc)

# AI Tutor (streaming)
@api_router.post("/ai/tutor")
async def ai_tutor(req: TutorRequest, request: Request):
    user = await get_current_user(request)
    doc = await db.documents.find_one({"_id": req.document_id, "user_id": user["id"], "is_deleted": False})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    text = doc.get("extracted_text", "")[:6000]
    
    mode_prompts = {
        "beginner": "Explain concepts in very simple terms, use analogies, and avoid jargon.",
        "intermediate": "Provide clear explanations with examples. Balance simplicity with accuracy.",
        "advanced": "Provide in-depth explanations. You can use technical terminology.",
        "exam_prep": "Focus on exam-relevant information, common pitfalls, and test strategies."
    }
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content found in document")

    system_msg = (
        "You are an English-speaking study tutor. Reply in standard English only. "
        "Use clear explanations, simple vocabulary, and concise structure. "
        f"{mode_prompts.get(req.difficulty_mode, mode_prompts['intermediate'])} "
        "Guide students with hints before giving direct answers. "
        "Answer only from the uploaded document text when it is relevant. If the document does not contain enough information, say so briefly and do not invent details. "
        f"Reference this material: {text}"
    )

    async def event_generator():
        try:
            async for delta in llm_stream(system=system_msg, prompt=req.question):
                if isinstance(delta, str) and delta.startswith("data: "):
                    yield delta
                else:
                    yield f"data: {json.dumps({'content': delta})}\n\n"
        except Exception as exc:
            logger.exception("Tutor streaming failed")
            yield f"data: {json.dumps({'error': 'The tutor could not answer this question right now. Please try again.'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

# Quiz generation
@api_router.post("/ai/quiz")
async def generate_quiz(req: QuizRequest, request: Request):
    user = await get_current_user(request)

    safe_question_count = max(3, min(int(req.num_questions or 3), 8))
    max_context_chars = 3200
    combined_text = ""
    for doc_id in req.document_ids[:3]:
        doc = await db.documents.find_one({"_id": doc_id, "user_id": user["id"], "is_deleted": False})
        if doc:
            combined_text += (doc.get("extracted_text", "")[:1200] + "\n\n")

    combined_text = combined_text[:max_context_chars]

    if not combined_text:
        raise HTTPException(status_code=400, detail="No text found in documents")

    question_types_str = ", ".join(req.question_types[:3])

    prompt = f"""Generate exactly {safe_question_count} concise quiz questions from this material.
Question types: {question_types_str}
Difficulty: {req.difficulty}

Rules:
- Use only the source material provided.
- Do not invent facts, authors, dates, or examples that do not appear in the text.
- Return valid JSON only.
- Each question must include: type, question, options (for multiple choice), correct_answer, explanation.
- For multiple choice, use exactly 4 options and a valid correct answer label such as "A".

Material:
{combined_text}

Return ONLY valid JSON in this exact shape:
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "..."
    }}
  ]
}}"""

    quiz_content = await llm_generate(
        system="You are a fast quiz generator. Return valid JSON only, with no markdown fences and no extra commentary. Keep questions short, clear, and focused on the most important ideas from the provided material.",
        prompt=prompt,
    )

    try:
        cleaned_quiz = strip_markdown_fences(quiz_content)
        quiz_data = json.loads(cleaned_quiz)
        quiz_data = validate_quiz_payload(quiz_data)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=f"The AI returned invalid quiz JSON: {exc}") from exc

    quiz_id = str(uuid.uuid4())
    quiz_doc = {
        "id": quiz_id,
        "user_id": user["id"],
        "document_ids": req.document_ids,
        "quiz_data": quiz_data,
        "difficulty": req.difficulty,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.quizzes.insert_one(quiz_doc)
    return normalize_supabase_id(quiz_doc) or dict(quiz_doc)

def _is_question_library_table_missing(err: Exception) -> bool:
    text = str(err).lower()
    return "could not find the table" in text or "pgrst205" in text or "does not exist" in text


def _get_question_library_sets_for_user(user_id: str) -> List[Dict[str, Any]]:
    rows = MEMORY_STORE.get("question_sets", [])
    return [normalize_supabase_id(dict(row)) or dict(row) for row in rows if str((row or {}).get("user_id")) == str(user_id)]


def _get_question_library_questions_for_user(user_id: str, set_id: str) -> List[Dict[str, Any]]:
    rows = MEMORY_STORE.get("question_set_questions", [])
    return [normalize_supabase_id(dict(row)) or dict(row) for row in rows if str((row or {}).get("user_id")) == str(user_id) and str((row or {}).get("question_set_id")) == str(set_id)]


# Practice Question Library (minimal, user-scoped)
@api_router.post("/question-library/sets")
async def create_question_set(req: QuestionLibrarySetRequest, request: Request):
    user = await get_current_user(request)

    name = (req.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Question set name is required.")
    if not req.questions:
        raise HTTPException(status_code=400, detail="Question set must include at least one question.")

    try:
        validated_questions = [normalize_question_library_question(question) for question in req.questions]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    set_doc = {
        "id": set_id,
        "user_id": user["id"],
        "name": name,
        "subject": (req.subject or "").strip(),
        "topic": (req.topic or "").strip(),
        "difficulty": (req.difficulty or "medium").strip() or "medium",
        "question_type": (req.question_type or "multiple_choice").strip() or "multiple_choice",
        "created_at": now,
        "updated_at": now,
    }

    try:
        await db.question_sets.insert_one(set_doc)
    except Exception as exc:
        if not _is_question_library_table_missing(exc):
            raise
        MEMORY_STORE.setdefault("question_sets", []).append(dict(set_doc))

    stored_questions = []
    for question in validated_questions:
        question_item = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "question_set_id": set_id,
            "question": question["question"],
            "type": question["type"],
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer", question.get("answer", "")),
            "answer": question.get("answer", ""),
            "explanation": question.get("explanation", ""),
            "created_at": now,
        }
        try:
            await db.question_set_questions.insert_one(question_item)
        except Exception as exc:
            if not _is_question_library_table_missing(exc):
                raise
            MEMORY_STORE.setdefault("question_set_questions", []).append(dict(question_item))
        stored_questions.append(normalize_supabase_id(question_item) or dict(question_item))

    response = normalize_supabase_id(set_doc) or dict(set_doc)
    response["questions"] = stored_questions
    return response


@api_router.get("/question-library/sets")
async def list_question_sets(request: Request):
    user = await get_current_user(request)

    try:
        sets = await db.question_sets.find({"user_id": user["id"]}).sort([("updated_at", -1)]).to_list(1000)
    except Exception as exc:
        if not _is_question_library_table_missing(exc):
            raise
        sets = _get_question_library_sets_for_user(user["id"])

    results = []
    for set_doc in sets:
        normalized_set = normalize_supabase_id(set_doc) or dict(set_doc)
        normalized_set.pop("_id", None)
        try:
            question_items = await db.question_set_questions.find({
                "user_id": user["id"],
                "question_set_id": normalized_set["id"],
            }).to_list(1000)
        except Exception as exc:
            if not _is_question_library_table_missing(exc):
                raise
            question_items = _get_question_library_questions_for_user(user["id"], normalized_set["id"])
        normalized_set["questions"] = [
            normalize_supabase_id(item) or dict(item) for item in question_items
        ]
        results.append(normalized_set)
    return results


@api_router.post("/admin/library/import-default")
async def import_default_library_catalog_admin(request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    report = import_default_library_catalog(db=db)
    if report.get("failed") and any(report["failed"].values()):
        raise HTTPException(status_code=500, detail={"message": "Library import completed with failures", "report": report})
    return report


@api_router.get("/library/qualifications")
async def list_library_qualifications(request: Request):
    await get_current_user(request)
    catalog = _get_published_library_catalog()
    return catalog.get("qualifications", [])


@api_router.get("/library/qualifications/{qualification_slug}")
async def get_library_qualification(qualification_slug: str, request: Request):
    await get_current_user(request)
    catalog = _get_published_library_catalog()
    qualification = _find_library_qualification(catalog.get("qualifications", []), qualification_slug)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return qualification


@api_router.get("/library/qualifications/{qualification_slug}/subjects")
async def list_library_subjects(qualification_slug: str, request: Request):
    await get_current_user(request)
    catalog = _get_published_library_catalog()
    qualification = _find_library_qualification(catalog.get("qualifications", []), qualification_slug)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return qualification.get("subjects", [])


@api_router.get("/library/qualifications/{qualification_slug}/subjects/{subject_slug}")
async def get_library_subject(qualification_slug: str, subject_slug: str, request: Request):
    await get_current_user(request)
    catalog = _get_published_library_catalog()
    qualification = _find_library_qualification(catalog.get("qualifications", []), qualification_slug)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")

    subject = next((item for item in qualification.get("subjects", []) if str(item.get("slug")) == str(subject_slug)), None)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@api_router.get("/library/qualifications/{qualification_slug}/subjects/{subject_slug}/topics/{topic_slug}")
async def get_library_topic(qualification_slug: str, subject_slug: str, topic_slug: str, request: Request):
    await get_current_user(request)
    catalog = _get_published_library_catalog()
    qualification = _find_library_qualification(catalog.get("qualifications", []), qualification_slug)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")

    subject = next((item for item in qualification.get("subjects", []) if str(item.get("slug")) == str(subject_slug)), None)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    topic = next((item for item in subject.get("topics", []) if str(item.get("slug")) == str(topic_slug)), None)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return {"qualification": qualification, "subject": subject, "topic": topic}


# Flashcards
@api_router.post("/ai/flashcards")
async def generate_flashcards(req: FlashcardRequest, request: Request):
    user = await get_current_user(request)
    doc = await db.documents.find_one({"_id": req.document_id, "user_id": user["id"], "is_deleted": False})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    text = doc.get("extracted_text", "")[:5000]
    
    prompt = f"""Generate flashcards from this study material. Create 10-15 flashcards covering key concepts, definitions, and important facts.

Material:
{text}

Format as JSON:
{{
  "flashcards": [
    {{
      "front": "Question or term",
      "back": "Answer or definition",
      "hint": "Optional hint"
    }}
  ]
}}"""
    
    flashcard_content = await llm_generate(
        system="You are an expert at creating effective flashcards for studying. Always return valid JSON.",
        prompt=prompt,
    )
    
    try:
        if "```json" in flashcard_content:
            flashcard_content = flashcard_content.split("```json")[1].split("```")[0].strip()
        elif "```" in flashcard_content:
            flashcard_content = flashcard_content.split("```")[1].split("```")[0].strip()

        flashcard_data = json.loads(flashcard_content)
    except Exception:
        flashcard_data = {"flashcards": [], "error": "Failed to parse flashcards"}

    flashcard_set_id = str(uuid.uuid4())
    flashcard_doc = {
        "id": flashcard_set_id,
        "user_id": user["id"],
        "document_id": req.document_id,
        "document_name": doc.get("original_filename") or doc.get("filename") or doc.get("name") or "Untitled Document",
        "flashcards": flashcard_data.get("flashcards", []),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.flashcard_sets.insert_one(flashcard_doc)
    return normalize_supabase_id(flashcard_doc) or dict(flashcard_doc)

@api_router.get("/flashcards")
async def list_flashcards(request: Request):
    user = await get_current_user(request)
    flashcards = await db.flashcard_sets.find({"user_id": user["id"]}).to_list(1000)
    normalized_flashcards: List[Dict[str, Any]] = []
    for f in flashcards:
        normalized = ensure_response_id(f)
        if normalized is not None:
            normalized_flashcards.append(normalized)
    return normalized_flashcards

# Study planner
@api_router.post("/ai/study-plan")
async def generate_study_plan(req: StudyPlanRequest, request: Request):
    user = await get_current_user(request)
    
    user_profile = await db.users.find_one({"_id": user["id"]}, {"_id": 0}) or {}
    subjects = user_profile.get("subjects", [])
    curriculum = user_profile.get("curriculum", "")
    
    prompt = f"""Create a personalized study plan for a student.

Profile:
- Subjects: {', '.join(subjects)}
- Curriculum: {curriculum}
- Daily study time available: {req.daily_study_time} minutes
- Exam dates: {json.dumps(req.exam_dates)}

Create a weekly study schedule. Format as JSON:
{{
  "weeks": [
    {{
      "week_number": 1,
      "days": [
        {{
          "day": "Monday",
          "tasks": [
            {{
              "subject": "Math",
              "topic": "Algebra",
              "duration_minutes": 30,
              "task_type": "review"
            }}
          ]
        }}
      ]
    }}
  ]
}}"""
    
    plan_content = await llm_generate(
        system="You are an expert study planner. Create realistic, balanced study schedules. Always return valid JSON.",
        prompt=prompt,
    )
    
    try:
        if "```json" in plan_content:
            plan_content = plan_content.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_content:
            plan_content = plan_content.split("```")[1].split("```")[0].strip()
        
        plan_data = json.loads(plan_content)
    except Exception:
        plan_data = {"weeks": [], "error": "Failed to parse study plan"}
    
    plan_id = str(uuid.uuid4())
    plan_doc = {
        "id": plan_id,
        "user_id": user["id"],
        "plan_data": plan_data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.study_plans.insert_one(plan_doc)
    return normalize_supabase_id(plan_doc) or dict(plan_doc)

@api_router.get("/study-plan/current")
async def get_current_study_plan(request: Request):
    user = await get_current_user(request)
    plan = await db.study_plans.find_one({"user_id": user["id"]}, sort=[("created_at", -1)])
    if not plan:
        return {"plan_data": {"weeks": []}}
    plan = ensure_response_id(plan) or plan
    return plan

# Progress tracking
@api_router.get("/progress/stats")
async def get_progress_stats(request: Request):
    user = await get_current_user(request)
    
    doc_count = await db.documents.count_documents({"user_id": user["id"], "is_deleted": False})
    quiz_count = await db.quizzes.count_documents({"user_id": user["id"]})
    flashcard_count = await db.flashcard_sets.count_documents({"user_id": user["id"]})
    
    streak = await db.streaks.find_one({"user_id": user["id"]}, {"_id": 0})
    if not streak:
        streak = {"current_streak": 0, "longest_streak": 0, "total_study_minutes": 0}
    
    return {
        "documents_uploaded": doc_count,
        "quizzes_taken": quiz_count,
        "flashcards_created": flashcard_count,
        "current_streak": streak.get("current_streak", 0),
        "longest_streak": streak.get("longest_streak", 0),
        "total_study_minutes": streak.get("total_study_minutes", 0)
    }

@api_router.post("/progress/log-activity")
async def log_activity(request: Request, activity_data: Dict[str, Any]):
    user = await get_current_user(request)
    
    today = datetime.now(timezone.utc).date().isoformat()
    current_streak = 1
    
    streak = await db.streaks.find_one({"user_id": user["id"]})
    if streak:
        last_date = streak.get("last_activity_date")
        current_streak = streak.get("current_streak", 0)
        longest_streak = streak.get("longest_streak", 0)
        total_minutes = streak.get("total_study_minutes", 0)
        
        if last_date != today:
            if last_date == (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat():
                current_streak += 1
            else:
                current_streak = 1
            
            longest_streak = max(longest_streak, current_streak)
            
            await db.streaks.update_one(
                {"user_id": user["id"]},
                {"$set": {
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "last_activity_date": today,
                    "total_study_minutes": total_minutes + activity_data.get("study_minutes", 0)
                }}
            )
    else:
        streak_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "current_streak": 1,
            "longest_streak": 1,
            "last_activity_date": today,
            "total_study_minutes": activity_data.get("study_minutes", 0)
        }
        await db.streaks.insert_one(streak_doc)
    
    return {"message": "Activity logged", "current_streak": current_streak}

# Notes endpoints
@api_router.post("/notes")
async def create_note(req: NoteRequest, request: Request):
    user = await get_current_user(request)
    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    note_doc = {
        "id": note_id,
        "user_id": user["id"],
        "title": req.title,
        "content": req.content,
        "tags": req.tags,
        "color": req.color,
        "is_pinned": req.is_pinned,
        "document_id": req.document_id,
        "created_at": now,
        "updated_at": now,
    }
    await db.notes.insert_one(note_doc)
    return normalize_supabase_id(note_doc) or dict(note_doc)

@api_router.get("/notes")
async def list_notes(request: Request):
    user = await get_current_user(request)
    notes = await db.notes.find({"user_id": user["id"]}).sort([("is_pinned", -1), ("updated_at", -1)]).to_list(1000)
    normalized_notes: List[Dict[str, Any]] = []
    for n in notes:
        normalized = ensure_response_id(n)
        if normalized is not None:
            normalized_notes.append(normalized)
    return normalized_notes

@api_router.get("/notes/{note_id}")
async def get_note(note_id: str, request: Request):
    user = await get_current_user(request)
    note = await db.notes.find_one({"_id": note_id, "user_id": user["id"]})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note = ensure_response_id(note) or note
    return note

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, req: NoteRequest, request: Request):
    user = await get_current_user(request)
    result = await db.notes.update_one(
        {"_id": note_id, "user_id": user["id"]},
        {"$set": {
            "title": req.title,
            "content": req.content,
            "tags": req.tags,
            "color": req.color,
            "is_pinned": req.is_pinned,
            "document_id": req.document_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    note = await db.notes.find_one({"_id": note_id, "user_id": user["id"]})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note = ensure_response_id(note) or note
    return note

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.notes.delete_one({"_id": note_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}

@api_router.get("/dashboard")
async def get_dashboard(request: Request):
    user = await get_current_user(request)
    
    recent_docs = await db.documents.find(
        {"user_id": user["id"], "is_deleted": False},
        {"extracted_text": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    normalized_recent_docs: List[Dict[str, Any]] = []
    for d in recent_docs:
        normalized = ensure_response_id(d)
        if normalized is not None:
            normalized_recent_docs.append(normalized)
    recent_docs = normalized_recent_docs

    stats = await get_progress_stats(request)
    
    study_plan = await db.study_plans.find_one({"user_id": user["id"]}, sort=[("created_at", -1)])
    
    return {
        "recent_documents": recent_docs,
        "stats": stats,
        "study_plan": study_plan.get("plan_data", {"weeks": []}) if study_plan else {"weeks": []}
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    # When running locally with credentials, default to common localhost origins
    # Include ports used by CRA (3000) and Vite (5173) and their 127.0.0.1 equivalents
    allow_origins=os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

async def seed_admin():
    app_env = (os.environ.get("APP_ENV") or "development").lower()
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if app_env == "production" and not admin_email and not admin_password:
        logger.warning("Production mode: skipping default admin account creation because ADMIN_EMAIL and ADMIN_PASSWORD are not configured.")
        return

    admin_email = admin_email or "admin@studyai.com"
    admin_password = admin_password or "admin123"

    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        admin_id = str(uuid.uuid4())
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "id": admin_id,
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "role": "admin",
            "onboarded": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info(f"Admin password updated")

    if app_env != "production":
        # Write test credentials to the repository-local memory directory so startup
        # succeeds on systems where /app is not writable.
        mem_dir = ROOT_DIR / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        with open(mem_dir / "test_credentials.md", "w") as f:
            f.write(f"""# Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Endpoints
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout
- POST /api/auth/onboarding
- POST /api/documents/upload
- GET /api/documents
- POST /api/ai/summary
- POST /api/ai/tutor
- POST /api/ai/quiz
- POST /api/ai/flashcards
- POST /api/ai/study-plan
- GET /api/progress/stats
- GET /api/dashboard
""")

@app.on_event("startup")
async def startup():
    logger.info(f"Local storage directory: {STORAGE_DIR}")
    logger.info(f"Using OpenRouter model: {OPENAI_MODEL}")


    await seed_admin()

    await db.users.create_index("email", unique=True)
    await db.documents.create_index("user_id")
    await db.summaries.create_index("document_id")
    await db.quizzes.create_index("user_id")
    await db.flashcard_sets.create_index("user_id")
    await db.study_plans.create_index("user_id")
    await db.streaks.create_index("user_id")
    await db.notes.create_index("user_id")

    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    return None
