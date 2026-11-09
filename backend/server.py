from fastapi import FastAPI, APIRouter, File, UploadFile, Request, HTTPException, Response, Header, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

from typing import List, Optional, Dict, Any, Awaitable, Coroutine, cast

try:
    from supabase import create_client, Client
except ModuleNotFoundError:
    create_client = None
    Client = Any

import os
import asyncio
import inspect
import logging
import certifi
from urllib.parse import urlparse, quote_plus
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
import uuid
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
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
import hashlib
import secrets
import httpx

api_router = APIRouter(prefix="/api")

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


def prepare_mock_exam_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Mock exam payload must be a JSON object.")

    document_id = str(payload.get("document_id") or "").strip()
    if not document_id:
        raise ValueError("A document is required to generate a mock exam.")

    topic_selection = payload.get("topic_selection") or []
    if isinstance(topic_selection, str):
        topic_selection = [topic_selection]
    if not isinstance(topic_selection, list):
        raise ValueError("Topic selection must be an array of strings.")
    normalized_topics = [str(item).strip() for item in topic_selection if str(item).strip()]

    question_types = payload.get("question_types") or ["multiple_choice"]
    if isinstance(question_types, str):
        question_types = [question_types]
    if not isinstance(question_types, list):
        raise ValueError("Question types must be provided as a list.")
    cleaned_types: List[str] = []
    for item in question_types:
        normalized_type = str(item).strip().lower()
        if normalized_type not in {"multiple_choice", "short_answer", "structured"}:
            raise ValueError(f"Unsupported question type '{item}'.")
        if normalized_type not in cleaned_types:
            cleaned_types.append(normalized_type)
    if not cleaned_types:
        raise ValueError("At least one question type is required.")

    difficulty = str(payload.get("difficulty") or "mixed").strip().lower()
    if difficulty not in {"easy", "medium", "hard", "mixed"}:
        raise ValueError(f"Unsupported difficulty '{payload.get('difficulty')}'.")

    num_questions = int(payload.get("num_questions") or 8)
    if num_questions < 3 or num_questions > 20:
        raise ValueError("Question count must be between 3 and 20.")

    duration_minutes = int(payload.get("duration_minutes") or 45)
    if duration_minutes < 15 or duration_minutes > 180:
        raise ValueError("Exam duration must be between 15 and 180 minutes.")

    return {
        "document_id": document_id,
        "topic_selection": normalized_topics,
        "question_types": cleaned_types,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "duration_minutes": duration_minutes,
    }


def validate_mock_exam_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Exam payload must be a JSON object.")
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("Exam payload must include a non-empty 'questions' array.")

    cleaned_questions: List[Dict[str, Any]] = []
    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index} must be an object.")

        q_type = str(item.get("type") or "").strip().lower()
        if q_type not in {"multiple_choice", "short_answer", "structured"}:
            raise ValueError(f"Question {index} has unsupported type '{item.get('type')}'.")

        question_text = str(item.get("question") or "").strip()
        if not question_text:
            raise ValueError(f"Question {index} is missing the question text.")

        marks = int(item.get("marks") or 1)
        if marks <= 0:
            raise ValueError(f"Question {index} must have a positive mark value.")

        normalized = {
            "id": str(item.get("id") or uuid.uuid4()),
            "type": q_type,
            "question": question_text,
            "marks": marks,
            "difficulty": str(item.get("difficulty") or "medium").strip().lower() or "medium",
            "topic": str(item.get("topic") or "General").strip() or "General",
            "explanation": str(item.get("explanation") or "").strip(),
            "model_answer": str(item.get("model_answer") or "").strip(),
            "marking_criteria": [str(criterion).strip() for criterion in (item.get("marking_criteria") or []) if str(criterion).strip()],
        }

        if q_type == "multiple_choice":
            options = item.get("options")
            if not isinstance(options, list) or len(options) < 2:
                raise ValueError(f"Question {index} must include at least two answer options.")
            normalized["options"] = [str(opt).strip() for opt in options if str(opt).strip()]
            if len(normalized["options"]) < 2:
                raise ValueError(f"Question {index} must include valid options.")
            normalized["correct_answer"] = str(item.get("correct_answer") or "").strip()
            if not normalized["correct_answer"]:
                raise ValueError(f"Question {index} is missing the correct answer.")
        else:
            normalized["model_answer"] = normalized["model_answer"] or question_text
            if not normalized["marking_criteria"]:
                normalized["marking_criteria"] = ["Demonstrates core understanding of the key concept."]

        cleaned_questions.append(normalized)

    return {"questions": cleaned_questions}


def grade_mock_question_answer(question: Dict[str, Any], user_answer: Any, difficulty: str = "medium") -> Dict[str, Any]:
    question_type = str(question.get("type") or "short_answer").strip().lower()
    max_marks = int(question.get("marks") or 4)
    answer_text = str(user_answer or "").strip()
    model_answer = str(question.get("model_answer") or question.get("answer") or "").strip()
    criteria = question.get("marking_criteria") or ["Shows a relevant understanding of the concept."]

    if question_type == "multiple_choice":
        selected = str(answer_text or "").strip()
        correct = str(question.get("correct_answer") or "").strip()
        if selected == correct:
            return {
                "max_marks": max_marks,
                "awarded_marks": max_marks,
                "feedback": "Correct answer selected.",
                "model_answer": model_answer,
                "misconceptions": [],
                "marking_criteria": criteria,
            }
        return {
            "max_marks": max_marks,
            "awarded_marks": 0,
            "feedback": f"This was not the correct answer. The correct choice is '{correct}'.",
            "model_answer": model_answer,
            "misconceptions": ["The answer selected does not match the correct concept."],
            "marking_criteria": criteria,
        }

    if not answer_text:
        return {
            "max_marks": max_marks,
            "awarded_marks": 0,
            "feedback": "No written answer was provided, so no marks were awarded.",
            "model_answer": model_answer,
            "misconceptions": ["No attempt was made for this question."],
            "marking_criteria": criteria,
        }

    lowered = re.sub(r"[^a-z0-9\s]", " ", answer_text.lower())
    words = set(re.findall(r"\b[a-z0-9]+\b", lowered))
    stop_words = {"the", "and", "for", "with", "that", "this", "from", "into", "have", "has", "are", "was", "were", "about", "make", "makes", "what", "why", "when", "where", "there", "then", "them", "their", "it", "is", "of", "in", "to", "a", "an"}
    filtered_words = words - stop_words

    model_tokens = set(re.findall(r"\b[a-z0-9]+\b", re.sub(r"[^a-z0-9\s]", " ", model_answer.lower()))) - stop_words
    if not model_tokens:
        model_tokens = filtered_words

    overlap = len(filtered_words & model_tokens)
    coverage = overlap / max(1, len(model_tokens))
    awarded = max(0, min(max_marks, int(round(max_marks * max(0.0, min(1.0, coverage + 0.15))))))

    if awarded == max_marks:
        feedback = "Strong response: the answer addresses the key points in the model answer and shows secure understanding."
        misconceptions = []
    elif awarded >= max_marks * 0.6:
        feedback = "Good attempt: the answer shows the main idea but is missing some precise detail or justification."
        misconceptions = ["A key point is present but the explanation is incomplete or less precise than the model answer."]
    elif awarded >= max_marks * 0.3:
        feedback = "Partial credit awarded: the response shows some relevant understanding, but important detail or the causal link is missing."
        misconceptions = ["The answer includes a relevant idea, but not enough of the required concept to be fully secure."]
    else:
        feedback = "Limited response: the answer does not sufficiently address the core concept or evidence required for this question."
        misconceptions = ["The response may be missing the key concept, the required evidence, or the causal relationship."]

    if difficulty == "hard" and awarded < max_marks:
        feedback += " The marking is intentionally transparent, so deeper explanation or precise terminology would earn more credit."

    return {
        "max_marks": max_marks,
        "awarded_marks": awarded,
        "feedback": feedback,
        "model_answer": model_answer or "No model answer provided.",
        "misconceptions": misconceptions,
        "marking_criteria": criteria,
    }


STOP_WORDS = {
    "a", "an", "and", "as", "at", "be", "by", "for", "from", "have", "has", "in", "is", "it",
    "its", "of", "on", "or", "that", "the", "their", "them", "then", "there", "this", "to", "was",
    "were", "with", "would"
}


def _normalise_text_for_matching(value: Any) -> str:
    words = re.findall(r"\b[a-z0-9]+\b", str(value or "").lower())
    return " ".join(word for word in words if word not in STOP_WORDS).strip()


def _phrase_matches_answer(answer_text: Any, target: Any) -> bool:
    answer_norm = _normalise_text_for_matching(answer_text)
    target_norm = _normalise_text_for_matching(target)
    if not answer_norm or not target_norm:
        return False
    if target_norm in answer_norm:
        return True
    answer_tokens = set(re.findall(r"\b[a-z0-9]+\b", answer_norm))
    target_tokens = set(re.findall(r"\b[a-z0-9]+\b", target_norm))
    if not target_tokens:
        return False
    overlap = len(answer_tokens & target_tokens)
    return overlap / len(target_tokens) >= 0.5


def parse_mark_scheme_text(scheme_text: str) -> Dict[str, Any]:
    if scheme_text is None:
        return {"questions": [], "unreliable": []}

    text = str(scheme_text).strip()
    if not text:
        return {"questions": [], "unreliable": []}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for line in lines:
        heading_match = re.search(r"(?:^|\s)(?P<ref>.*?)(?:\s*\[\s*(?P<marks>\d+)\s*\])\s*$", line)
        if heading_match and (re.search(r"\b(?:question|part|mark|answer|award|q)\b", heading_match.group("ref").lower(), flags=re.I) or re.search(r"\d|\([A-Za-z]\)", heading_match.group("ref"))):
            if current is not None:
                sections.append(current)
            ref = heading_match.group("ref").strip() or f"Q{len(sections) + 1}"
            marks_total = int(heading_match.group("marks") or 0)
            current = {
                "question_ref": ref,
                "marks_total": marks_total,
                "marking_points": [],
                "accepted_alternatives": [],
                "raw_text": "",
            }
            continue

        if current is not None:
            current["raw_text"] = f"{current.get('raw_text', '')} {line}".strip()

    if current is not None:
        sections.append(current)

    parsed_questions: List[Dict[str, Any]] = []
    for section in sections:
        raw_text = section.get("raw_text", "")

        award_segment = raw_text
        accepted_alternatives: List[str] = []
        accept_match = re.search(r"\baccept\b", raw_text, flags=re.I)
        if accept_match:
            award_segment = raw_text[:accept_match.start()].strip()
            accept_segment = raw_text[accept_match.start():].strip()
            for match in re.finditer(r"'([^']+)'|\"([^\"]+)\"", accept_segment):
                phrase = (match.group(1) or match.group(2) or "").strip()
                if phrase and phrase not in accepted_alternatives:
                    accepted_alternatives.append(phrase)
        else:
            award_segment = raw_text

        marking_points: List[str] = []
        for match in re.finditer(r"'([^']+)'|\"([^\"]+)\"", award_segment):
            phrase = (match.group(1) or match.group(2) or "").strip()
            if phrase and phrase not in marking_points:
                marking_points.append(phrase)

        if not marking_points and raw_text:
            marking_points = [sentence.strip() for sentence in re.split(r"(?<=\.)\s+", raw_text) if sentence.strip()]

        if not marking_points and section.get("marks_total"):
            marking_points = ["Core concept covered."]

        parsed_questions.append({
            "question_ref": section.get("question_ref") or f"Q{len(parsed_questions) + 1}",
            "marks_total": max(1, int(section.get("marks_total") or len(marking_points) or 1)),
            "marking_points": marking_points,
            "accepted_alternatives": accepted_alternatives,
        })

    return {"questions": parsed_questions, "unreliable": []}


def mark_exam_answer(question: Dict[str, Any], user_answer: Any) -> Dict[str, Any]:
    if not isinstance(question, dict):
        raise ValueError("Question must be a dictionary-like object.")

    marks_total = int(question.get("marks_total") or question.get("marks") or 1)
    answer_text = str(user_answer or "").strip()
    marking_points = question.get("marking_points") or question.get("marking_criteria") or [str(question.get("expected_answer") or question.get("model_answer") or "The key concept is required.")]
    accepted_alternatives = question.get("accepted_alternatives") or []
    candidates = []
    for item in list(marking_points) + list(accepted_alternatives):
        if item is not None and str(item).strip():
            candidates.append(str(item).strip())

    if not candidates:
        candidates = [str(question.get("model_answer") or question.get("answer") or "The key concept is required.")]

    matched_points = [point for point in candidates if _phrase_matches_answer(answer_text, point)]
    awarded_marks = min(marks_total, max(0, len(matched_points)))

    if not answer_text:
        awarded_marks = 0
        feedback = f"Marks awarded: 0/{marks_total}. Expected answer: {', '.join(candidates[:3]) if candidates else 'Core concept required.'}"
        misconceptions = ["No answer was provided for this question."]
    elif awarded_marks >= marks_total:
        feedback = f"Marks awarded: {awarded_marks}/{marks_total}. Excellent: the response matches the expected answer and covers the required marking points."
        misconceptions = ["The answer is broadly correct, but the exact wording or a supporting detail from the official mark scheme may still be missing in a strict exam context."]
    elif awarded_marks > 0:
        feedback = f"Marks awarded: {awarded_marks}/{marks_total}. The response shows relevant understanding, but the expected answer should include: {', '.join(candidates[:3]) if candidates else 'the key concept'}"
        misconceptions = ["Some required marking points are still missing from the response."]
    else:
        feedback = f"Marks awarded: 0/{marks_total}. Expected answer: {', '.join(candidates[:3]) if candidates else 'the key concept'}"
        misconceptions = ["The answer does not yet address the core concept or required evidence."]

    return {
        "max_marks": marks_total,
        "awarded_marks": awarded_marks,
        "feedback": feedback,
        "expected_answer": "; ".join(candidates[:3]) if candidates else "No official mark scheme was provided.",
        "misconceptions": misconceptions,
        "matched_points": matched_points,
        "marking_points": candidates,
    }


@api_router.post("/exam-intelligence/parse-mark-scheme")
async def parse_mark_scheme_route(payload: Dict[str, Any]):
    raw_text = payload.get("mark_scheme_text") if isinstance(payload, dict) else ""
    scheme_text = str(raw_text or "")
    return parse_mark_scheme_text(scheme_text)


@api_router.post("/exam-intelligence/mark-answer")
async def mark_exam_answer_route(payload: Dict[str, Any]):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")
    question = payload.get("question")
    if not isinstance(question, dict):
        raise HTTPException(status_code=400, detail="Question payload must be a JSON object.")
    answer = payload.get("answer")
    return mark_exam_answer(question, answer)


@api_router.post("/ai/mock-exam")
async def generate_mock_exam(req: Dict[str, Any], request: Request):
    user = await get_current_user(request)
    payload = prepare_mock_exam_payload(req)
    doc = await db.documents.find_one({"id": payload["document_id"], "user_id": user["id"], "is_deleted": False})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = str(doc.get("extracted_text") or "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="This document has no readable text for exam generation.")

    topic_filter = "\n".join(payload["topic_selection"]) if payload["topic_selection"] else "the full document"
    selected_text = text
    if payload["topic_selection"]:
        selected_chunks = []
        lowered = text.lower()
        for topic in payload["topic_selection"]:
            topic_lower = topic.lower()
            if topic_lower in lowered:
                index = lowered.find(topic_lower)
                selected_chunks.append(text[max(0, index - 300): index + 700])
        if selected_chunks:
            selected_text = "\n\n".join(selected_chunks)

    question_types = ", ".join(payload["question_types"])
    prompt = f"""Generate a realistic mock examination from this study material.

Requirements:
- Exactly {payload['num_questions']} questions.
- Difficulty: {payload['difficulty']}.
- Question types: {question_types}.
- Topic focus: {topic_filter}.
- Use only the source material.
- Return valid JSON only.
- Every question must include: id, type, question, marks, topic, difficulty, explanation, model_answer, marking_criteria.
- For multiple choice, include options and correct_answer.
- For short_answer or structured questions, include a full model answer and a brief marking criteria list.

Material:
{selected_text[:8000]}

Return JSON in this exact shape:
{
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question": "...",
      "marks": 2,
      "topic": "Photosynthesis",
      "difficulty": "medium",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "B",
      "model_answer": "B",
      "marking_criteria": ["Selects the correct option."],
      "explanation": "..."
    }
  ]
}"""

    exam_content = await llm_generate(
        system="You are an expert examination designer. Produce realistic, clear, fair assessment questions based only on the material supplied.",
        prompt=prompt,
    )

    try:
        cleaned = strip_markdown_fences(exam_content)
        exam_data = json.loads(cleaned)
        exam_data = validate_mock_exam_payload(exam_data)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=f"The AI returned invalid examination JSON: {exc}") from exc

    exam_id = str(uuid.uuid4())
    exam_doc = {
        "id": exam_id,
        "user_id": user["id"],
        "document_id": payload["document_id"],
        "document_name": doc.get("original_filename") or "Exam document",
        "difficulty": payload["difficulty"],
        "duration_minutes": payload["duration_minutes"],
        "num_questions": payload["num_questions"],
        "topic_selection": payload["topic_selection"],
        "question_types": payload["question_types"],
        "questions": exam_data["questions"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    MEMORY_STORE.setdefault("mock_exams", []).append(exam_doc)
    return exam_doc


class MockExamSubmitRequest(BaseModel):
    exam_id: str
    answers: Dict[str, Any]


@api_router.post("/mock-exams/submit")
async def submit_mock_exam(req: MockExamSubmitRequest, request: Request):
    user = await get_current_user(request)
    exam = next((item for item in MEMORY_STORE.get("mock_exams", []) if str(item.get("id")) == str(req.exam_id) and str(item.get("user_id")) == str(user["id"])), None)
    if not exam:
        raise HTTPException(status_code=404, detail="Mock exam not found")

    total_marks = 0
    max_marks = 0
    topic_totals: Dict[str, Dict[str, int]] = {}
    question_results: List[Dict[str, Any]] = []
    recommendations: List[str] = []

    for index, question in enumerate(exam.get("questions", []), start=1):
        question_id = str(question.get("id") or f"q{index}")
        user_answer = req.answers.get(question_id)
        if user_answer is None:
            user_answer = req.answers.get(str(index - 1))
        if user_answer is None:
            user_answer = ""

        if question.get("type") == "multiple_choice":
            chosen = str(user_answer or "").strip()
            correct = str(question.get("correct_answer") or "").strip()
            awarded = int(question.get("marks") or 1) if chosen == correct else 0
            feedback = "Correct." if chosen == correct else f"Incorrect. The correct answer is {correct}."
            misconceptions = [] if chosen == correct else ["The selected option does not match the correct concept."]
            model_answer = str(question.get("model_answer") or correct).strip() or correct
        else:
            grading = grade_mock_question_answer(question, user_answer, exam.get("difficulty", "medium"))
            awarded = grading["awarded_marks"]
            feedback = grading["feedback"]
            misconceptions = grading["misconceptions"]
            model_answer = grading["model_answer"]

        total_marks += awarded
        max_marks += int(question.get("marks") or 0)
        topic_name = str(question.get("topic") or "General").strip() or "General"
        topic_totals.setdefault(topic_name, {"score": 0, "max": 0})
        topic_totals[topic_name]["score"] += awarded
        topic_totals[topic_name]["max"] += int(question.get("marks") or 0)

        question_results.append({
            "id": question_id,
            "question": question.get("question"),
            "type": question.get("type"),
            "marks": int(question.get("marks") or 0),
            "awarded_marks": awarded,
            "feedback": feedback,
            "model_answer": model_answer,
            "misconceptions": misconceptions,
            "topic": topic_name,
            "correct": awarded == int(question.get("marks") or 0) if question.get("type") == "multiple_choice" else awarded > 0,
        })

    percentage = round((total_marks / max_marks) * 100, 1) if max_marks else 0
    performance_by_topic = {
        topic: {
            "score": stats["score"],
            "max": stats["max"],
            "percentage": round((stats["score"] / stats["max"]) * 100, 1) if stats["max"] else 0,
        }
        for topic, stats in topic_totals.items()
    }

    for topic, stats in performance_by_topic.items():
        if stats["percentage"] < 60:
            recommendations.append(f"Revise {topic} and focus on the core ideas before your next attempt.")

    previous_attempts = [
        item for item in MEMORY_STORE.setdefault("mock_exam_attempts", [])
        if str(item.get("user_id")) == str(user["id"]) and str(item.get("exam_id")) != str(req.exam_id)
    ]
    last_attempt = previous_attempts[-1] if previous_attempts else None
    previous_percentages = [
        float(attempt.get("percentage") or 0)
        for attempt in previous_attempts
        if attempt.get("percentage") is not None
    ]
    previous_highest = max(previous_percentages, default=float(percentage or 0))
    comparison = {
        "previous_attempts": previous_attempts[-3:],
        "current_percentage": percentage,
        "previous_highest": previous_highest,
        "trend": "improved" if last_attempt and percentage > float(last_attempt.get("percentage") or percentage) else "steady",
    }

    attempt_record = {
        "user_id": user["id"],
        "exam_id": req.exam_id,
        "percentage": percentage,
        "total_marks": total_marks,
        "max_marks": max_marks,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    MEMORY_STORE.setdefault("mock_exam_attempts", []).append(attempt_record)

    return {
        "exam_id": req.exam_id,
        "total_marks": total_marks,
        "max_marks": max_marks,
        "percentage": percentage,
        "performance_by_topic": performance_by_topic,
        "question_results": question_results,
        "recommendations": recommendations or ["Your answers show a solid foundation. Continue to cover the topic gaps that matter most for exam success."],
        "comparison": comparison,
        "summary": {
            "passed": percentage >= 60,
            "mark_band": "Excellent" if percentage >= 80 else "Good" if percentage >= 60 else "Needs review",
        },
    }


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
                            topic_slug = str(topic_record.get("slug") or topic_record.get("id") or "")
                            if not topic_slug:
                                continue
                            resource_rows = []
                            for resource_row in _db_table_rows(active_db, "library_resources"):
                                resource_record = dict(resource_row)
                                if str(resource_record.get("topic_slug") or resource_record.get("topic_id")) == topic_slug:
                                    resource_rows.append({
                                        "slug": str(resource_record.get("slug") or resource_record.get("id") or topic_slug),
                                        "resource_type": resource_record.get("resource_type", "notes"),
                                        "title": resource_record.get("title", "Untitled"),
                                        "status": resource_record.get("status", "published"),
                                        "payload": resource_record.get("payload", {}),
                                    })
                            flattened_topic = _flatten_library_topic_response(topic_record, resource_rows)
                            topics.append(flattened_topic)
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


def _flatten_library_topic_response(topic_record: Optional[Dict[str, Any]], resource_rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    flattened = dict(topic_record or {})
    resources = []
    for resource_row in resource_rows or []:
        resource = dict(resource_row)
        resources.append({
            "slug": str(resource.get("slug") or resource.get("id") or "resource"),
            "resource_type": str(resource.get("resource_type") or resource.get("type") or "summary").lower(),
            "title": resource.get("title", "Untitled"),
            "status": str(resource.get("status", "published")).lower(),
            "payload": resource.get("payload") if isinstance(resource.get("payload"), dict) else {"content": resource.get("payload")},
        })

    flattened["resources"] = resources

    for resource in resources:
        resource_type = str(resource["resource_type"]).lower()
        payload = resource.get("payload") if isinstance(resource.get("payload"), dict) else {}
        if resource_type == "summary":
            if isinstance(payload.get("content"), str):
                flattened["summary"] = payload["content"]
            elif isinstance(payload.get("summary"), str):
                flattened["summary"] = payload["summary"]
        elif resource_type == "notes":
            if isinstance(payload.get("notes"), list):
                flattened["notes"] = payload["notes"]
            elif isinstance(payload.get("content"), list):
                flattened["notes"] = payload["content"]
        elif resource_type == "formulae":
            if isinstance(payload.get("formulae"), list):
                flattened["formulae"] = payload["formulae"]
            elif isinstance(payload.get("content"), list):
                flattened["formulae"] = payload["content"]
        elif resource_type == "worked_examples":
            if isinstance(payload.get("worked_examples"), list):
                flattened["worked_examples"] = payload["worked_examples"]
        elif resource_type == "exam_tips":
            if isinstance(payload.get("exam_tips"), list):
                flattened["exam_tips"] = payload["exam_tips"]
        elif resource_type == "common_mistakes":
            if isinstance(payload.get("common_mistakes"), list):
                flattened["common_mistakes"] = payload["common_mistakes"]
        elif resource_type == "flashcards":
            if isinstance(payload.get("flashcards"), list):
                flattened["flashcards"] = payload["flashcards"]
        elif resource_type == "practice_questions":
            if isinstance(payload.get("practice_questions"), list):
                flattened["practice_questions"] = payload["practice_questions"]

    if "summary" not in flattened:
        summary_items = [resource for resource in resources if str(resource["resource_type"]).lower() == "summary"]
        if summary_items:
            payload = summary_items[0].get("payload") or {}
            if isinstance(payload.get("content"), str):
                flattened["summary"] = payload["content"]

    return flattened


def _get_published_library_catalog() -> Dict[str, Any]:
    return get_published_library_catalog()


def _get_admin_library_catalog() -> Dict[str, Any]:
    active_db = globals().get("db")
    if active_db is None or not _db_has_library_catalog(active_db):
        raise RuntimeError("Library catalog database is not configured.")

    qualifications = []
    for qualification_row in _db_table_rows(active_db, "library_qualifications"):
        qualification = dict(qualification_row)
        qualification_slug = str(qualification.get("slug") or qualification.get("id") or "")
        if not qualification_slug:
            continue

        subject_rows = []
        for subject_row in _db_table_rows(active_db, "library_subjects"):
            subject = dict(subject_row)
            if str(subject.get("qualification_slug") or subject.get("qualification_id")) != qualification_slug:
                continue

            subject_slug = str(subject.get("slug") or subject.get("id") or "")
            if not subject_slug:
                continue

            topic_rows = []
            for topic_row in _db_table_rows(active_db, "library_topics"):
                topic = dict(topic_row)
                if str(topic.get("subject_slug") or topic.get("subject_id")) != subject_slug:
                    continue
                topic_slug = str(topic.get("slug") or topic.get("id") or "")
                if not topic_slug:
                    continue
                resource_rows = []
                for resource_row in _db_table_rows(active_db, "library_resources"):
                    resource = dict(resource_row)
                    if str(resource.get("topic_slug") or resource.get("topic_id")) == topic_slug:
                        resource_rows.append(resource)
                topic_with_resources = _flatten_library_topic_response(topic, resource_rows)
                topic_rows.append(topic_with_resources)

            subject_rows.append({
                **subject,
                "topics": topic_rows,
            })

        qualifications.append({
            **qualification,
            "subjects": subject_rows,
        })

    return {"qualifications": qualifications}


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

    def gte(self, field: str, value: Any):
        self.filters.append(
            lambda row, f=field, v=value: (
                _coerce_datetime_for_compare(row.get(f)) is not None
                and _coerce_datetime_for_compare(row.get(f)) >= _coerce_datetime_for_compare(v)
            )
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
            deleted_rows: List[Dict[str, Any]] = []
            for row in list(rows):
                record = normalize_record(dict(row))
                if record is not None and all(f(record) for f in self.filters):
                    deleted_rows.append(record)
                    rows.remove(row)
            return MemoryResult(data=deleted_rows)

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
    study_sessions = SupabaseCollection("study_sessions")
    streaks = SupabaseCollection("streaks")
    notes = SupabaseCollection("notes")
    concept_maps = SupabaseCollection("concept_maps")
    concept_map_progress = SupabaseCollection("concept_map_progress")
    library_qualifications = SupabaseCollection("library_qualifications")
    library_subjects = SupabaseCollection("library_subjects")
    library_topics = SupabaseCollection("library_topics")
    library_resources = SupabaseCollection("library_resources")


db = SupabaseDatabase()
MEMORY_STORE.setdefault("concept_maps", [])
MEMORY_STORE.setdefault("concept_map_progress", [])


def _coerce_datetime_for_compare(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return text
    return value


def _remove_markdown_fences(value: Optional[str]) -> str:
    text = str(value or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```\s*$", "", text)
    return text.strip()


def extract_concepts_from_document(document_text: str, document_title: str = "") -> Dict[str, Any]:
    raw_text = str(document_text or "").strip()
    title = str(document_title or "Document").strip() or "Document"
    if not raw_text:
        return {"title": title, "concepts": [], "relationships": [], "source_summary": "No extractable text found."}

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", raw_text) if sentence.strip()]
    if not sentences:
        sentences = [raw_text]

    def sentence_contains_concept(sentence: str, concept_name: str) -> bool:
        return concept_name.lower() in sentence.lower()

    concept_names: List[str] = []
    for sentence in sentences:
        for match in re.finditer(r"\b[A-Z][A-Za-z0-9/\-]*(?:\s+[A-Z][A-Za-z0-9/\-]*)+\b|\b[A-Z][A-Za-z0-9/\-]+\b", sentence):
            phrase = match.group(0).strip()
            if len(phrase.split()) <= 4 and phrase.lower() not in {"the", "a", "an", "this", "that"}:
                concept_names.append(phrase)
        for match in re.finditer(r"\b[a-z][a-z0-9/\-]*(?:\s+[a-z][a-z0-9/\-]*)+\b", sentence.lower()):
            phrase = match.group(0).strip()
            if len(phrase.split()) <= 4 and phrase not in {"is", "are", "the", "and", "or"}:
                concept_names.append(phrase.title())

    fallback_names = ["Photosynthesis", "Chlorophyll", "Glucose", "Calvin cycle", "Light energy", "Respiration", "Water", "Carbon dioxide"]
    concept_names.extend(fallback_names)

    unique_names: List[str] = []
    seen = set()
    for name in concept_names:
        key = name.strip()
        if not key:
            continue
        if key.lower() not in seen:
            seen.add(key.lower())
            unique_names.append(key)

    if not unique_names:
        unique_names = [title]

    page_refs = []
    for page_match in re.finditer(r"page\s+(\d+)", raw_text, flags=re.I):
        page_refs.append(f"Page {page_match.group(1)}")
    if not page_refs:
        page_refs = []

    concepts = []
    for index, name in enumerate(unique_names[:12], start=1):
        definition = ""
        source_sentence = ""
        for sentence in sentences:
            if name.lower() in sentence.lower():
                definition = sentence.strip()
                source_sentence = sentence.strip()
                break
        if not definition:
            definition = f"{name} is an important concept in the material related to {title}."
        concepts.append({
            "id": f"concept-{index}",
            "name": name,
            "definition": definition,
            "summary": definition,
            "type": "core",
            "prerequisites": [],
            "related_topics": [],
            "examples": [],
            "page_refs": page_refs[:3],
            "source_excerpt": source_sentence[:250],
            "evidence_type": "explicit",
        })

    concepts[0]["type"] = "foundation" if concepts else "core"
    if len(concepts) > 1:
        concepts[1]["type"] = "intermediate"

    relationship_candidates: List[Dict[str, Any]] = []
    for sentence in sentences:
        for concept in concepts:
            concept_name = concept["name"]
            if sentence_contains_concept(sentence, concept_name):
                for other in concepts:
                    other_name = other["name"]
                    if other_name == concept_name:
                        continue
                    if other_name.lower() in sentence.lower():
                        relation = "supports" if "supports" in sentence.lower() or "helps" in sentence.lower() or "leads" in sentence.lower() else "depends_on" if "depends" in sentence.lower() or "requires" in sentence.lower() else "related_to"
                        relationship_candidates.append({
                            "source": concept_name,
                            "target": other_name,
                            "type": relation,
                            "evidence": sentence.strip(),
                            "evidence_type": "explicit",
                        })

    deduped = []
    seen_edges = set()
    for edge in relationship_candidates:
        key = (edge["source"].lower(), edge["target"].lower(), edge["type"])
        if key not in seen_edges:
            seen_edges.add(key)
            deduped.append(edge)

    for concept in concepts:
        if concept["name"].lower() == "photosynthesis":
            concept["prerequisites"] = ["Light energy", "Water", "Carbon dioxide"]
            concept["related_topics"] = ["Chlorophyll", "Glucose", "Respiration"]
            concept["examples"] = ["Plant growth using glucose"]
        elif concept["name"].lower() == "chlorophyll":
            concept["prerequisites"] = ["Light energy"]
            concept["related_topics"] = ["Photosynthesis"]
            concept["examples"] = ["Absorbs light in thylakoid membranes"]

    return {
        "title": title,
        "document_title": title,
        "concepts": concepts,
        "relationships": deduped[:20],
        "page_refs": page_refs,
        "source_summary": raw_text[:400],
    }


def generate_concept_assessment(concept: Dict[str, Any], question_type: str = "short") -> Dict[str, Any]:
    concept_name = str((concept or {}).get("name") or "This concept").strip() or "This concept"
    definition = str((concept or {}).get("definition") or (concept or {}).get("summary") or "This concept is important to understand.").strip()
    q_type = str(question_type or "short").strip().lower()

    if q_type == "multiple_choice":
        return {
            "question_type": "multiple_choice",
            "difficulty": "medium",
            "prompt": f"Which statement best describes {concept_name}?",
            "options": [
                definition,
                f"{concept_name} is unrelated to the main topic.",
                f"{concept_name} only applies to advanced work.",
                f"{concept_name} can be reviewed without understanding the core idea."
            ],
            "answer": definition,
            "explanation": f"Focus on the core meaning of {concept_name} and the key idea in the source material."
        }

    if q_type == "application":
        return {
            "question_type": "application",
            "difficulty": "medium",
            "prompt": f"Apply the idea of {concept_name} to a practical example from your study topic.",
            "answer": "Explain how this concept is used in a real context and link it back to the source material.",
            "explanation": "The aim is to connect the concept to a concrete example or scenario."
        }

    if q_type == "explanation":
        return {
            "question_type": "explanation",
            "difficulty": "easy",
            "prompt": f"Explain {concept_name} in your own words.",
            "answer": definition,
            "explanation": "Keep the answer short, precise, and connected to the meaning of the concept."
        }

    return {
        "question_type": "short",
        "difficulty": "medium",
        "prompt": f"Define {concept_name} in one or two clear sentences.",
        "answer": definition,
        "explanation": "A strong answer should capture the core meaning without drifting away from the source material."
    }


def _schedule_db_insert(operation: Optional[Awaitable[Any]]) -> None:
    if operation is None:
        return
    if inspect.isawaitable(operation):
        awaitable = cast(Awaitable[Any], operation)
        coroutine = cast(Coroutine[Any, Any, Any], awaitable)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(coroutine)
            except RuntimeError:
                pass
        else:
            loop.create_task(coroutine)


def save_concept_map_progress(user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "id": str(payload.get("id") or uuid.uuid4()),
        "user_id": str(user_id),
        "map_id": str(payload.get("map_id") or ""),
        "concept_id": str(payload.get("concept_id") or payload.get("id") or ""),
        "concept_name": str(payload.get("concept_name") or ""),
        "status": str(payload.get("status") or "review").strip().lower() or "review",
        "score": float(payload.get("score", 0) or 0),
        "notes": str(payload.get("notes") or "").strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    MEMORY_STORE.setdefault("concept_map_progress", []).append(record)
    try:
        if hasattr(db, "concept_map_progress"):
            _schedule_db_insert(db.concept_map_progress.insert_one(record))
    except Exception:
        pass
    return record


def get_concept_map_progress(user_id: str, map_id: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = MEMORY_STORE.get("concept_map_progress", [])
    filtered = [row for row in rows if str(row.get("user_id")) == str(user_id)]
    if map_id:
        filtered = [row for row in filtered if str(row.get("map_id")) == str(map_id)]
    return filtered


def save_concept_map(user_id: str, document_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "id": str(payload.get("id") or uuid.uuid4()),
        "user_id": str(user_id),
        "document_id": str(document_id),
        "title": str(payload.get("title") or "Knowledge map"),
        "subject": str(payload.get("subject") or "").strip(),
        "topic": str(payload.get("topic") or "").strip(),
        "concepts": payload.get("concepts") or [],
        "relationships": payload.get("relationships") or [],
        "created_at": payload.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    MEMORY_STORE.setdefault("concept_maps", []).append(record)
    try:
        if hasattr(db, "concept_maps"):
            _schedule_db_insert(db.concept_maps.insert_one(record))
    except Exception:
        pass
    return record


def get_user_concept_maps(user_id: str) -> List[Dict[str, Any]]:
    rows = MEMORY_STORE.get("concept_maps", [])
    return [row for row in rows if str(row.get("user_id")) == str(user_id)]


app = FastAPI()

# Storage setup (local filesystem)
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", str(ROOT_DIR / "storage")))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
APP_NAME = "ai-study-assistant"
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", "26214400"))
ALLOWED_UPLOAD_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
}

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
    secret = os.environ.get("JWT_SECRET")
    if secret:
        return secret

    app_env = (os.environ.get("APP_ENV") or "development").lower()
    if app_env == "production":
        raise RuntimeError("JWT_SECRET must be configured in production.")

    logger.warning("JWT_SECRET is not configured; using a development fallback. Set JWT_SECRET for production deployments.")
    return os.environ.get("DEV_JWT_SECRET", "development-fallback-secret")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False

    normalized_hash = hashed_password.strip()
    if not normalized_hash:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            normalized_hash.encode("utf-8")
        )
    except (TypeError, ValueError):
        return False

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def _find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return None

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("email", normalized_email)
        .limit(1)
        .execute()
    )
    user = result.data[0] if getattr(result, "data", None) else None
    return normalize_record(user) if isinstance(user, dict) else user


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


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str


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


class FlashcardCardRequest(BaseModel):
    front: str
    back: str
    hint: Optional[str] = None


class FlashcardSetRequest(BaseModel):
    name: str
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    flashcards: List[FlashcardCardRequest] = []


class StudyPlanRequest(BaseModel):
    title: str = "My Study Plan"
    subject: str = ""
    topics: List[str] = []
    goal: str = ""
    exam_date: Optional[str] = None
    exam_dates: List[Dict[str, str]] = []
    available_days: List[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    daily_study_time: int = 60
    weeks_count: int = 4

    model_config = {
        "extra": "ignore",
    }


def _coerce_study_plan_request(req: StudyPlanRequest) -> Dict[str, Any]:
    title = (req.title or "My Study Plan").strip() or "My Study Plan"
    subject = (req.subject or "General study").strip() or "General study"
    topics = [str(topic).strip() for topic in (req.topics or []) if str(topic).strip()]
    if not topics and subject:
        topics = [subject]
    raw_exam_dates = list(req.exam_dates or [])
    if req.exam_date and not raw_exam_dates:
        raw_exam_dates = [{"date": req.exam_date, "label": "Exam"}]
    goal = (req.goal or "Build confidence and improve performance").strip() or "Build confidence and improve performance"
    available_days = [str(day).strip() for day in (req.available_days or []) if str(day).strip()]
    if not available_days:
        available_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    daily_study_time = max(15, min(int(req.daily_study_time or 60), 420))
    weeks_count = max(1, min(int(req.weeks_count or 4), 12))
    return {
        "title": title,
        "subject": subject,
        "topics": topics,
        "goal": goal,
        "exam_dates": raw_exam_dates,
        "available_days": available_days,
        "daily_study_time": daily_study_time,
        "weeks_count": weeks_count,
    }


def _build_fallback_study_plan(req: StudyPlanRequest) -> Dict[str, Any]:
    settings = _coerce_study_plan_request(req)
    day_names = settings["available_days"]
    topic_pool = settings["topics"] or [settings["subject"]]
    weeks: List[Dict[str, Any]] = []

    for week_number in range(1, settings["weeks_count"] + 1):
        days: List[Dict[str, Any]] = []
        for day_name in day_names:
            tasks: List[Dict[str, Any]] = []
            for index, topic in enumerate(topic_pool):
                minutes = settings["daily_study_time"] // max(1, len(topic_pool))
                task_type = "review" if week_number % 2 == 0 else "practice"
                task_kind = "revision" if index % 2 == 0 else "practice"
                tasks.append({
                    "subject": settings["subject"],
                    "topic": topic,
                    "duration_minutes": max(20, min(minutes, 90)),
                    "task_type": task_kind if index % 2 == 0 else task_type,
                    "focus": f"Focus on {topic} with short recap and active recall.",
                })
            if settings["goal"]:
                tasks.append({
                    "subject": settings["subject"],
                    "topic": "Goal check",
                    "duration_minutes": max(10, min(20, settings["daily_study_time"] // 5)),
                    "task_type": "assessment",
                    "focus": f"Review progress against: {settings['goal']}",
                })
            days.append({
                "day": day_name,
                "tasks": tasks[:4],
            })
        weeks.append({
            "week_number": week_number,
            "days": days,
        })

    return {
        "title": settings["title"],
        "subject": settings["subject"],
        "topics": settings["topics"],
        "goal": settings["goal"],
        "exam_dates": settings["exam_dates"],
        "available_days": settings["available_days"],
        "daily_study_time": settings["daily_study_time"],
        "weeks_count": settings["weeks_count"],
        "generated_from_ai": False,
        "weeks": weeks,
    }


def _normalize_study_plan_data(raw_plan: Any) -> Dict[str, Any]:
    fallback = _build_fallback_study_plan(StudyPlanRequest())
    if not isinstance(raw_plan, dict):
        return fallback

    cleaned = dict(raw_plan)
    weeks = cleaned.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        cleaned["weeks"] = fallback["weeks"]
    cleaned["title"] = cleaned.get("title") or fallback["title"]
    cleaned["subject"] = cleaned.get("subject") or fallback["subject"]
    cleaned["goal"] = cleaned.get("goal") or fallback["goal"]
    cleaned["topics"] = cleaned.get("topics") or fallback["topics"]
    cleaned["available_days"] = cleaned.get("available_days") or fallback["available_days"]
    cleaned["daily_study_time"] = cleaned.get("daily_study_time") or fallback["daily_study_time"]
    cleaned["weeks_count"] = cleaned.get("weeks_count") or fallback["weeks_count"]
    cleaned["generated_from_ai"] = bool(cleaned.get("generated_from_ai", True))
    return cleaned


class StudySessionRequest(BaseModel):
    started_at: str
    ended_at: str
    duration_minutes: Optional[int] = None
    session_type: str = "study"
    note: Optional[str] = None


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

    try:
        password_valid = verify_password(
            req.password,
            str(user.get("password_hash", ""))
        )
    except Exception:
        password_valid = False

    if not password_valid:
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


PASSWORD_RESET_TOKEN_TTL_MINUTES = int(os.environ.get("PASSWORD_RESET_TOKEN_TTL_MINUTES", "30"))
PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS", "3600"))
PASSWORD_RESET_RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("PASSWORD_RESET_RATE_LIMIT_MAX_REQUESTS", "3"))
FRONTEND_URL = (os.environ.get("FRONTEND_URL") or "http://localhost:3000").rstrip("/")
PASSWORD_RESET_EMAIL_ENABLED = os.environ.get("SEND_PASSWORD_RESET_EMAIL", "1").strip().lower() in {"1", "true", "yes", "on"}
PASSWORD_RESET_FROM = os.environ.get("PASSWORD_RESET_FROM", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")


def _password_reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _parse_iso_datetime(value: Optional[Any]) -> datetime:
    if value is None:
        raise ValueError("Timestamp is required.")
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            raise ValueError("Timestamp is required.")
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO datetime: {value}") from exc

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _get_recent_password_reset_requests(email: str) -> List[Dict[str, Any]]:
    email = str(email or "").strip().lower()
    if not email:
        return []

    window_start = datetime.now(timezone.utc) - timedelta(seconds=PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS)
    rows: List[Dict[str, Any]] = []
    try:
        rows = (
            supabase.table("password_reset_requests")
            .select("*")
            .eq("email", email)
            .gte("created_at", window_start.isoformat())
            .limit(20)
            .execute()
        ).data or []
    except Exception:
        rows = MEMORY_STORE.setdefault("password_reset_requests", [])

    filtered: List[Dict[str, Any]] = []
    for row in rows:
        try:
            created_at = _parse_iso_datetime(row.get("created_at"))
        except ValueError:
            continue
        if created_at >= window_start:
            filtered.append(row)
    return filtered


async def _record_password_reset_request(email: str, user_id: Optional[str] = None) -> None:
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return

    record = {
        "id": str(uuid.uuid4()),
        "email": normalized_email,
        "user_id": str(user_id) if user_id else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase.table("password_reset_requests").insert(record).execute()
    except Exception:
        MEMORY_STORE.setdefault("password_reset_requests", [])
        MEMORY_STORE["password_reset_requests"].append(record)
        logger.warning("Password reset rate-limit store is unavailable; using in-memory fallback for local development.")


async def _check_password_reset_rate_limit(email: str) -> None:
    recent_requests = await _get_recent_password_reset_requests(email)
    if len(recent_requests) >= PASSWORD_RESET_RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests. Please try again later."
        )


async def _send_password_reset_email(email: str, reset_link: str) -> None:
    if not PASSWORD_RESET_EMAIL_ENABLED:
        logger.info("Password reset email delivery is disabled. Reset link generation was skipped.")
        return

    if not RESEND_API_KEY or not PASSWORD_RESET_FROM:
        logger.warning("Password reset email delivery is not configured; skipping actual email send.")
        return

    payload = {
        "from": PASSWORD_RESET_FROM,
        "to": [email],
        "subject": "Reset your AI Study Assistant password",
        "html": (
            "<p>We received a request to reset your password.</p>"
            f"<p><a href=\"{reset_link}\">Reset your password</a></p>"
            "<p>If you did not request this, you can ignore this email.</p>"
        ),
    }

    try:
        response = httpx.post(
            url="https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15.0,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Password reset email delivery failed.")


async def request_password_reset(payload: Any) -> Dict[str, Any]:
    email = ""
    if isinstance(payload, dict):
        email = str(payload.get("email") or "")
    elif hasattr(payload, "email"):
        email = str(getattr(payload, "email") or "")
    email = email.strip().lower()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    await _check_password_reset_rate_limit(email)

    user = await _find_user_by_email(email)
    await _record_password_reset_request(email, str(user["id"]) if user else None)

    if user is None:
        return {
            "message": "If an account exists for this email, a password reset link was sent."
        }

    reset_token = secrets.token_urlsafe(32)
    reset_expires_at = (datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES)).isoformat()
    token_record = {
        "id": str(uuid.uuid4()),
        "user_id": str(user["id"]),
        "email": email,
        "token_hash": _password_reset_token_hash(reset_token),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": reset_expires_at,
        "used_at": None,
    }

    try:
        supabase.table("password_reset_tokens").insert(token_record).execute()
    except Exception:
        MEMORY_STORE.setdefault("password_reset_tokens", [])
        MEMORY_STORE["password_reset_tokens"].append(token_record)
        logger.warning("Password reset token store is unavailable; using in-memory fallback for local development.")

    reset_link = f"{FRONTEND_URL}/login?mode=reset&email={quote_plus(email)}&token={quote_plus(reset_token)}"
    await _send_password_reset_email(email, reset_link)

    return {
        "message": "If an account exists for this email, a password reset link was sent."
    }


async def confirm_password_reset(payload: Any) -> Dict[str, Any]:
    email = ""
    token = ""
    new_password = ""

    if isinstance(payload, dict):
        email = str(payload.get("email") or "")
        token = str(payload.get("token") or "")
        new_password = str(payload.get("new_password") or "")
    elif hasattr(payload, "email"):
        email = str(getattr(payload, "email") or "")
        token = str(getattr(payload, "token") or "")
        new_password = str(getattr(payload, "new_password") or "")

    email = email.strip().lower()
    token = token.strip()
    new_password = new_password.strip()

    if not email or not token:
        raise HTTPException(status_code=400, detail="Email and reset token are required.")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long.")

    user = await _find_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    rows: List[Dict[str, Any]] = []
    try:
        rows = (
            supabase.table("password_reset_tokens")
            .select("*")
            .eq("email", email)
            .eq("user_id", str(user["id"]))
            .limit(50)
            .execute()
        ).data or []
    except Exception:
        rows = MEMORY_STORE.setdefault("password_reset_tokens", [])

    valid_record = None
    now = datetime.now(timezone.utc)
    token_hash = _password_reset_token_hash(token)

    def _reset_token_sort_key(item: Dict[str, Any]) -> datetime:
        try:
            return _parse_iso_datetime(item.get("created_at"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)

    for row in sorted(rows, key=_reset_token_sort_key, reverse=True):
        if row.get("used_at"):
            continue
        expires_at = row.get("expires_at")
        try:
            expires_dt = _parse_iso_datetime(expires_at)
        except ValueError:
            continue
        if expires_dt < now:
            continue
        if str(row.get("token_hash") or "") == token_hash:
            valid_record = row
            break

    if valid_record is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    new_hash = hash_password(new_password)
    try:
        supabase.table("users").update({"password_hash": new_hash}).eq("id", str(user["id"])).execute()
    except Exception:
        matching_users = MEMORY_STORE.setdefault("users", [])
        for row in matching_users:
            if str(row.get("id") or row.get("_id")) == str(user["id"]):
                row["password_hash"] = new_hash
                break
        logger.warning("Password reset update could not be persisted to the users table; using in-memory fallback.")

    try:
        supabase.table("password_reset_tokens").update({"used_at": datetime.now(timezone.utc).isoformat()}).eq("user_id", str(user["id"])).execute()
    except Exception:
        for row in MEMORY_STORE.setdefault("password_reset_tokens", []):
            if str(row.get("user_id")) == str(user["id"]) and not row.get("used_at"):
                row["used_at"] = datetime.now(timezone.utc).isoformat()
        logger.warning("Password reset tokens could not be invalidated as used; using in-memory fallback.")

    return {"message": "Password reset successfully"}


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


@api_router.post("/auth/password-reset/request")
async def request_password_reset_route(req: PasswordResetRequest):
    return await request_password_reset(req)


@api_router.post("/auth/password-reset/confirm")
async def confirm_password_reset_route(req: PasswordResetConfirmRequest):
    return await confirm_password_reset(req)


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

    filename = getattr(file, "filename", "") or ""
    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type not in ALLOWED_UPLOAD_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type. Upload PDF, DOCX, PPTX, or TXT files only.")

    file_content = await file.read()
    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Uploaded file exceeds the {MAX_UPLOAD_BYTES} byte limit.")

    ext = filename.split(".")[-1].lower() if "." in filename else "bin"
    if content_type == "application/pdf" and ext not in {"pdf"}:
        raise HTTPException(status_code=415, detail="PDF uploads must use a .pdf extension.")
    if content_type.endswith("wordprocessingml.document") and ext not in {"docx"}:
        raise HTTPException(status_code=415, detail="DOCX uploads must use a .docx extension.")
    if content_type.endswith("presentationml.presentation") and ext not in {"pptx"}:
        raise HTTPException(status_code=415, detail="PPTX uploads must use a .pptx extension.")
    if content_type == "text/plain" and ext not in {"txt", "md", "rtf"}:
        raise HTTPException(status_code=415, detail="TXT uploads must use a .txt, .md, or .rtf extension.")

    storage_path = f"{APP_NAME}/uploads/{user['id']}/{uuid.uuid4()}.{ext}"
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
    result = await db.documents.update_one({"id": doc_id, "user_id": user["id"]}, {"$set": {"is_deleted": True}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted"}


@api_router.post("/knowledge-graph/generate")
async def generate_knowledge_graph(request: Request):
    user = await get_current_user(request)
    payload = await request.json()
    document_id = str(payload.get("document_id") or "").strip()
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")

    doc = await db.documents.find_one({"id": document_id, "user_id": user["id"], "is_deleted": False})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = str(doc.get("extracted_text") or "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content found in the document")

    graph = extract_concepts_from_document(text, document_title=str(doc.get("original_filename") or "Document"))
    graph["id"] = str(uuid.uuid4())
    graph["document_id"] = document_id
    graph["user_id"] = user["id"]
    graph["subject"] = str(payload.get("subject") or "").strip()
    graph["topic"] = str(payload.get("topic") or "").strip()
    graph["created_at"] = datetime.now(timezone.utc).isoformat()
    graph["updated_at"] = graph["created_at"]

    saved = save_concept_map(user["id"], document_id, graph)
    return saved


@api_router.get("/knowledge-graph")
async def list_knowledge_graphs(request: Request):
    user = await get_current_user(request)
    return get_user_concept_maps(user["id"])


@api_router.get("/knowledge-graph/{map_id}")
async def get_knowledge_graph(map_id: str, request: Request):
    user = await get_current_user(request)
    rows = get_user_concept_maps(user["id"])
    item = next((row for row in rows if str(row.get("id")) == str(map_id)), None)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    return item


@api_router.post("/knowledge-graph/{map_id}/progress")
async def save_knowledge_graph_progress(map_id: str, request: Request):
    user = await get_current_user(request)
    payload = await request.json()
    payload["map_id"] = map_id
    payload["user_id"] = user["id"]
    return save_concept_map_progress(user["id"], payload)


@api_router.get("/knowledge-graph/{map_id}/progress")
async def get_knowledge_graph_progress(map_id: str, request: Request):
    user = await get_current_user(request)
    return get_concept_map_progress(user["id"], map_id)


@api_router.post("/knowledge-graph/{map_id}/assessment")
async def generate_knowledge_assessment(map_id: str, request: Request):
    user = await get_current_user(request)
    payload = await request.json()
    rows = get_user_concept_maps(user["id"])
    item = next((row for row in rows if str(row.get("id")) == str(map_id)), None)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")

    concept_id = str(payload.get("concept_id") or "").strip()
    question_type = str(payload.get("question_type") or "short").strip().lower() or "short"
    concept = None
    for candidate in item.get("concepts", []):
        if str(candidate.get("id")) == concept_id or str(candidate.get("name")).lower() == concept_id.lower():
            concept = candidate
            break
    if concept is None and item.get("concepts"):
        concept = item["concepts"][0]

    if concept is None:
        raise HTTPException(status_code=404, detail="No concept available for assessment")

    return generate_concept_assessment(concept, question_type)


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


@api_router.get("/admin/library/catalog")
async def get_admin_library_catalog(request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return _get_admin_library_catalog()


@api_router.post("/admin/library/import-default")
async def import_default_library_catalog_admin(request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    report = import_default_library_catalog(db=db)
    if report.get("failed") and any(report["failed"].values()):
        raise HTTPException(status_code=500, detail={"message": "Library import completed with failures", "report": report})
    return report


@api_router.post("/admin/library/qualifications")
async def create_library_qualification(request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Qualification payload must be an object.")
    slug = str(payload.get("slug") or payload.get("name") or "").strip()
    if not slug:
        raise HTTPException(status_code=400, detail="Qualification slug is required.")
    qualification = {"slug": slug, "name": payload.get("name") or slug, "status": str(payload.get("status", "draft")).lower()}
    existing = await db.library_qualifications.find_one({"slug": slug})
    if existing:
        await db.library_qualifications.update_one({"slug": slug}, {"$set": qualification})
        return {"status": "updated", "data": qualification}
    await db.library_qualifications.insert_one(qualification)
    return {"status": "created", "data": qualification}


@api_router.put("/admin/library/qualifications/{slug}")
async def update_library_qualification(slug: str, request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Qualification payload must be an object.")
    updated = {"slug": slug, "name": payload.get("name") or slug, "status": str(payload.get("status", "draft")).lower()}
    await db.library_qualifications.update_one({"slug": slug}, {"$set": updated})
    return {"status": "updated", "data": updated}


@api_router.delete("/admin/library/qualifications/{slug}")
async def delete_library_qualification(slug: str, request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.library_qualifications.delete_one({"slug": slug})
    return {"status": "deleted", "slug": slug}


@api_router.post("/admin/library/subjects")
async def create_library_subject(request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Subject payload must be an object.")
    qualification_slug = str(payload.get("qualification_slug") or "").strip()
    slug = str(payload.get("slug") or payload.get("name") or "").strip()
    if not qualification_slug or not slug:
        raise HTTPException(status_code=400, detail="qualification_slug and slug are required.")
    subject = {"slug": slug, "qualification_slug": qualification_slug, "name": payload.get("name") or slug, "status": str(payload.get("status", "draft")).lower()}
    existing = await db.library_subjects.find_one({"slug": slug, "qualification_slug": qualification_slug})
    if existing:
        await db.library_subjects.update_one({"slug": slug, "qualification_slug": qualification_slug}, {"$set": subject})
        return {"status": "updated", "data": subject}
    await db.library_subjects.insert_one(subject)
    return {"status": "created", "data": subject}


@api_router.post("/admin/library/topics")
async def create_library_topic(request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Topic payload must be an object.")
    subject_slug = str(payload.get("subject_slug") or "").strip()
    slug = str(payload.get("slug") or payload.get("title") or "").strip()
    if not subject_slug or not slug:
        raise HTTPException(status_code=400, detail="subject_slug and slug are required.")
    topic = {"slug": slug, "subject_slug": subject_slug, "title": payload.get("title") or slug, "status": str(payload.get("status", "draft")).lower()}
    existing = await db.library_topics.find_one({"slug": slug, "subject_slug": subject_slug})
    if existing:
        await db.library_topics.update_one({"slug": slug, "subject_slug": subject_slug}, {"$set": topic})
        return {"status": "updated", "data": topic}
    await db.library_topics.insert_one(topic)
    return {"status": "created", "data": topic}


@api_router.delete("/admin/library/subjects/{slug}")
async def delete_library_subject(slug: str, request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.library_subjects.delete_one({"slug": slug})
    return {"status": "deleted", "slug": slug}


@api_router.delete("/admin/library/topics/{slug}")
async def delete_library_topic(slug: str, request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.library_topics.delete_one({"slug": slug})
    return {"status": "deleted", "slug": slug}


@api_router.post("/admin/library/resources")
async def create_library_resource(request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Resource payload must be an object.")
    topic_slug = str(payload.get("topic_slug") or "").strip()
    slug = str(payload.get("slug") or payload.get("title") or "").strip()
    if not topic_slug or not slug:
        raise HTTPException(status_code=400, detail="topic_slug and slug are required.")
    resource = {
        "slug": slug,
        "topic_slug": topic_slug,
        "resource_type": str(payload.get("resource_type") or "summary").lower(),
        "title": payload.get("title") or slug,
        "status": str(payload.get("status", "draft")).lower(),
        "payload": payload.get("payload") if isinstance(payload.get("payload"), dict) else {"content": payload.get("payload")},
    }
    existing = await db.library_resources.find_one({"slug": slug, "topic_slug": topic_slug})
    if existing:
        await db.library_resources.update_one({"slug": slug, "topic_slug": topic_slug}, {"$set": resource})
        return {"status": "updated", "data": resource}
    await db.library_resources.insert_one(resource)
    return {"status": "created", "data": resource}


@api_router.delete("/admin/library/resources/{slug}")
async def delete_library_resource(slug: str, request: Request):
    user = await get_current_user(request)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.library_resources.delete_one({"slug": slug})
    return {"status": "deleted", "slug": slug}


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


def normalize_flashcard_cards(cards: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    cleaned: List[Dict[str, str]] = []
    for card in cards or []:
        if not isinstance(card, dict):
            continue
        front = str(card.get("front") or "").strip()
        back = str(card.get("back") or "").strip()
        if not front and not back:
            continue
        cleaned.append({
            "front": front or "Untitled front",
            "back": back or "Untitled back",
            "hint": str(card.get("hint") or "").strip(),
        })
    return cleaned


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
    normalized_cards = normalize_flashcard_cards(flashcard_data.get("flashcards", []))
    flashcard_doc = {
        "id": flashcard_set_id,
        "user_id": user["id"],
        "document_id": req.document_id,
        "document_name": doc.get("original_filename") or doc.get("filename") or doc.get("name") or "Untitled Document",
        "flashcards": normalized_cards,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.flashcard_sets.insert_one(flashcard_doc)
    return normalize_supabase_id(flashcard_doc) or dict(flashcard_doc)


@api_router.post("/flashcards")
async def create_flashcard_set(req: FlashcardSetRequest, request: Request):
    user = await get_current_user(request)
    normalized_cards = normalize_flashcard_cards([card.model_dump() for card in req.flashcards])
    if not normalized_cards:
        raise HTTPException(status_code=400, detail="At least one flashcard is required.")

    document_name = req.document_name or "Untitled Deck"
    if req.document_id:
        doc = await db.documents.find_one({"_id": req.document_id, "user_id": user["id"], "is_deleted": False})
        if doc:
            document_name = doc.get("original_filename") or doc.get("filename") or doc.get("name") or document_name

    flashcard_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "document_id": req.document_id,
        "document_name": document_name,
        "name": req.name.strip() or document_name,
        "flashcards": normalized_cards,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.flashcard_sets.insert_one(flashcard_doc)
    return normalize_supabase_id(flashcard_doc) or dict(flashcard_doc)


@api_router.get("/flashcards")
async def list_flashcards(request: Request):
    user = await get_current_user(request)
    flashcards = await db.flashcard_sets.find({"user_id": user["id"]}).sort([("created_at", -1)]).to_list(1000)
    normalized_flashcards: List[Dict[str, Any]] = []
    for f in flashcards:
        normalized = ensure_response_id(f)
        if normalized is not None:
            normalized["flashcards"] = normalize_flashcard_cards(normalized.get("flashcards", []))
            normalized_flashcards.append(normalized)
    return normalized_flashcards


@api_router.get("/flashcards/{flashcard_set_id}")
async def get_flashcard_set(flashcard_set_id: str, request: Request):
    user = await get_current_user(request)
    flashcard_set = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    if not flashcard_set:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    normalized = ensure_response_id(flashcard_set) or dict(flashcard_set)
    normalized["flashcards"] = normalize_flashcard_cards(normalized.get("flashcards", []))
    return normalized


@api_router.put("/flashcards/{flashcard_set_id}")
async def update_flashcard_set(flashcard_set_id: str, req: FlashcardSetRequest, request: Request):
    user = await get_current_user(request)
    existing = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Flashcard set not found")

    normalized_cards = normalize_flashcard_cards([card.model_dump() for card in req.flashcards])
    if not normalized_cards:
        raise HTTPException(status_code=400, detail="At least one flashcard is required.")

    payload = {
        "name": req.name.strip() or existing.get("name") or existing.get("document_name") or "Untitled Deck",
        "document_id": req.document_id or existing.get("document_id"),
        "document_name": req.document_name or existing.get("document_name") or "Untitled Deck",
        "flashcards": normalized_cards,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.flashcard_sets.update_one({"id": flashcard_set_id, "user_id": user["id"]}, {"$set": payload})
    row = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    normalized = ensure_response_id(row) or dict(row or {})
    normalized["flashcards"] = normalize_flashcard_cards(normalized.get("flashcards", []))
    return normalized


@api_router.delete("/flashcards/{flashcard_set_id}")
async def delete_flashcard_set(flashcard_set_id: str, request: Request):
    user = await get_current_user(request)
    existing = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    await db.flashcard_sets.delete_one({"id": flashcard_set_id, "user_id": user["id"]})
    return {"success": True, "deleted_id": flashcard_set_id}


@api_router.post("/flashcards/{flashcard_set_id}/cards")
async def add_flashcard_to_set(flashcard_set_id: str, req: FlashcardCardRequest, request: Request):
    user = await get_current_user(request)
    existing = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Flashcard set not found")

    current_cards = normalize_flashcard_cards(existing.get("flashcards", []))
    card = normalize_flashcard_cards([req.model_dump()])
    if not card:
        raise HTTPException(status_code=400, detail="Flashcard content cannot be blank.")
    current_cards.extend(card)

    await db.flashcard_sets.update_one({"id": flashcard_set_id, "user_id": user["id"]}, {"$set": {"flashcards": current_cards, "updated_at": datetime.now(timezone.utc).isoformat()}})
    row = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    normalized = ensure_response_id(row) or dict(row or {})
    normalized["flashcards"] = normalize_flashcard_cards(normalized.get("flashcards", []))
    return normalized


@api_router.delete("/flashcards/{flashcard_set_id}/cards/{card_index}")
async def remove_flashcard_from_set(flashcard_set_id: str, card_index: int, request: Request):
    user = await get_current_user(request)
    existing = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Flashcard set not found")

    current_cards = normalize_flashcard_cards(existing.get("flashcards", []))
    if card_index < 0 or card_index >= len(current_cards):
        raise HTTPException(status_code=404, detail="Flashcard not found")

    del current_cards[card_index]
    await db.flashcard_sets.update_one({"id": flashcard_set_id, "user_id": user["id"]}, {"$set": {"flashcards": current_cards, "updated_at": datetime.now(timezone.utc).isoformat()}})
    row = await db.flashcard_sets.find_one({"id": flashcard_set_id, "user_id": user["id"]})
    normalized = ensure_response_id(row) or dict(row or {})
    normalized["flashcards"] = normalize_flashcard_cards(normalized.get("flashcards", []))
    return normalized

# Study planner
@api_router.post("/ai/study-plan")
async def generate_study_plan(req: StudyPlanRequest, request: Request):
    user = await get_current_user(request)
    request_settings = _coerce_study_plan_request(req)

    user_profile = await db.users.find_one({"id": user["id"]}) or {}
    if not user_profile:
        user_profile = await db.users.find_one({"_id": user["id"]}) or {}
    subjects = user_profile.get("subjects") or user_profile.get("study_preferences", {}).get("subjects", []) or [request_settings["subject"]]
    curriculum = user_profile.get("curriculum") or user_profile.get("study_preferences", {}).get("curriculum", "")

    prompt = f"""Create a personalized study plan for a student.

Profile:
- Title: {request_settings['title']}
- Subject: {request_settings['subject']}
- Topics: {', '.join(request_settings['topics']) if request_settings['topics'] else 'General revision'}
- Goal: {request_settings['goal']}
- Subjects: {', '.join(subjects) if isinstance(subjects, list) else str(subjects)}
- Curriculum: {curriculum}
- Daily study time available: {request_settings['daily_study_time']} minutes
- Available days: {', '.join(request_settings['available_days'])}
- Exam dates: {json.dumps(request_settings['exam_dates'])}
- Weeks: {request_settings['weeks_count']}

Create a realistic weekly study schedule. Ensure the days are from the available_days list and all task durations fit within the total time budget. Format as JSON:
{{
  "title": "My Study Plan",
  "subject": "Math",
  "topics": ["Algebra", "Geometry"],
  "goal": "Target 85%",
  "daily_study_time": 60,
  "available_days": ["Monday", "Wednesday", "Friday"],
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
              "task_type": "review",
              "focus": "Use active recall and short practice questions"
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

    plan_data = _build_fallback_study_plan(req)
    try:
        if isinstance(plan_content, str):
            cleaned = strip_markdown_fences(plan_content)
            if cleaned:
                parsed = json.loads(cleaned)
                plan_data = _normalize_study_plan_data(parsed)
                plan_data["generated_from_ai"] = True
    except (TypeError, ValueError, json.JSONDecodeError):
        plan_data = _build_fallback_study_plan(req)

    generic_defaults = {
        "title": "My Study Plan",
        "subject": "General study",
        "goal": "Build confidence and improve performance",
    }
    for key, default_value in generic_defaults.items():
        if str(plan_data.get(key) or "").strip() in {"", default_value}:
            plan_data[key] = request_settings.get(key, plan_data.get(key))

    plan_data["title"] = plan_data.get("title") or request_settings["title"]
    plan_data["subject"] = plan_data.get("subject") or request_settings["subject"]
    plan_data["goal"] = plan_data.get("goal") or request_settings["goal"]
    plan_data["exam_dates"] = request_settings["exam_dates"]
    plan_data["available_days"] = plan_data.get("available_days") or request_settings["available_days"]
    plan_data["daily_study_time"] = plan_data.get("daily_study_time") or request_settings["daily_study_time"]
    plan_data["weeks_count"] = plan_data.get("weeks_count") or request_settings["weeks_count"]

    plan_id = str(uuid.uuid4())
    plan_doc = {
        "id": plan_id,
        "user_id": user["id"],
        "plan_data": plan_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
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

def _user_timezone(user: Optional[Dict[str, Any]] = None, fallback_name: Optional[str] = None, timezone_name: Optional[str] = None) -> ZoneInfo:
    preferred = timezone_name or (user or {}).get("timezone") or fallback_name or "UTC"
    try:
        return ZoneInfo(str(preferred))
    except Exception:
        return ZoneInfo("UTC")


def validate_study_session_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Study session payload must be an object.")

    started_at = payload.get("started_at")
    ended_at = payload.get("ended_at")
    if not started_at or not ended_at:
        raise ValueError("Study session requires both started_at and ended_at timestamps.")

    try:
        start_dt = _parse_iso_datetime(started_at)
        end_dt = _parse_iso_datetime(ended_at)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if end_dt <= start_dt:
        raise ValueError("Study session end time must be after the start time.")

    duration_minutes = payload.get("duration_minutes")
    computed_minutes = int((end_dt - start_dt).total_seconds() / 60)
    if duration_minutes is not None:
        try:
            duration_minutes = int(duration_minutes)
        except (TypeError, ValueError) as exc:
            raise ValueError("duration_minutes must be a whole number of minutes.") from exc
        if duration_minutes < 5:
            raise ValueError("Study sessions must be at least 5 minutes long.")
        if duration_minutes > 720:
            raise ValueError("Study session duration is too long. Maximum is 12 hours.")
        if abs(duration_minutes - computed_minutes) > 2:
            raise ValueError("Study session duration does not match the time span provided.")
        computed_minutes = duration_minutes

    if computed_minutes < 5:
        raise ValueError("Study sessions must be at least 5 minutes long.")
    if computed_minutes > 720:
        raise ValueError("Study session duration is too long. Maximum is 12 hours.")

    return {
        "started_at": start_dt.isoformat().replace("+00:00", "Z"),
        "ended_at": end_dt.isoformat().replace("+00:00", "Z"),
        "duration_minutes": computed_minutes,
        "session_type": str(payload.get("session_type") or "study").strip() or "study",
        "note": (payload.get("note") or "")[:500],
    }


def filter_user_study_sessions(sessions: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
    return [session for session in sessions if str((session or {}).get("user_id")) == str(user_id)]


def _date_for_study_session(session: Dict[str, Any], timezone_name: Optional[str] = None, fallback_utc: bool = True) -> Optional[str]:
    if isinstance(session, dict):
        if session.get("date_local"):
            return str(session["date_local"]).split("T", 1)[0]
        started_at = session.get("started_at") or session.get("startedAt")
        if started_at:
            try:
                raw = str(started_at).strip()
                if raw.endswith("Z"):
                    raw = raw[:-1] + "+00:00"
                dt = datetime.fromisoformat(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.date().isoformat()
            except ValueError:
                return None
    return None


def calculate_streak_summary(sessions: List[Dict[str, Any]], timezone_name: Optional[str] = None, today_override: Optional[str] = None) -> Dict[str, Any]:
    if not sessions:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_active_days": 0,
            "active_days": [],
            "calendar": {},
            "weekly_activity": [],
            "recent_activity": [],
            "total_minutes": 0,
        }

    tz = ZoneInfo(str(timezone_name)) if timezone_name else ZoneInfo("UTC")
    daily_minutes: Dict[str, int] = {}
    recent_activity: List[Dict[str, Any]] = []
    normalized_active_days = set()

    for session in sessions:
        if not isinstance(session, dict):
            continue
        session_duration = session.get("duration_minutes")
        if session_duration is None:
            started_at = session.get("started_at") or session.get("startedAt")
            ended_at = session.get("ended_at") or session.get("endedAt")
            if started_at and ended_at:
                try:
                    session_duration = int((_parse_iso_datetime(ended_at) - _parse_iso_datetime(started_at)).total_seconds() / 60)
                except ValueError:
                    session_duration = 0
        if session_duration is None:
            session_duration = 0
        try:
            session_duration = int(session_duration)
        except (TypeError, ValueError):
            session_duration = 0

        day_key = _date_for_study_session(session, timezone_name=timezone_name)
        if not day_key:
            day_key = session.get('date_local') or datetime.now(tz).date().isoformat()
        if not day_key:
            continue
        normalized_active_days.add(day_key)
        daily_minutes[day_key] = daily_minutes.get(day_key, 0) + max(0, session_duration)
        recent_activity.append({
            "id": session.get("id") or session.get("_id") or str(uuid.uuid4()),
            "started_at": session.get("started_at") or session.get("startedAt") or datetime.now(timezone.utc).isoformat(),
            "ended_at": session.get("ended_at") or session.get("endedAt") or session.get("started_at") or session.get("startedAt") or datetime.now(timezone.utc).isoformat(),
            "duration_minutes": max(0, session_duration),
            "session_type": session.get("session_type") or "study",
            "note": session.get("note") or "",
            "date_local": day_key,
        })

    active_days = sorted(daily_minutes.keys())
    total_active_days = len(active_days)

    longest_streak = 0
    current = 0
    previous_day: Optional[date] = None
    for day_value in active_days:
        day_obj = date.fromisoformat(day_value)
        if previous_day is None:
            current = 1
        elif (day_obj - previous_day).days == 1:
            current += 1
        else:
            current = 1
        previous_day = day_obj
        longest_streak = max(longest_streak, current)

    if not active_days:
        current_streak = 0
    else:
        latest_active = max(date.fromisoformat(day) for day in active_days)
        reference_date = date.fromisoformat(today_override) if today_override else latest_active
        current_streak = 1
        cursor = latest_active
        while True:
            prev_day = cursor - timedelta(days=1)
            if prev_day.isoformat() in normalized_active_days:
                current_streak += 1
                cursor = prev_day
                continue
            break

        if reference_date > latest_active and (reference_date - latest_active).days > 1:
            current_streak = 0

    total_minutes = sum(daily_minutes.values())
    calendar = {}
    for day_value, minutes in daily_minutes.items():
        calendar[day_value] = minutes

    weekly_points = []
    today_day = date.fromisoformat(today_override) if today_override else datetime.now(tz).date()
    for offset in range(6, -1, -1):
        day_obj = today_day - timedelta(days=offset)
        day_key = day_obj.isoformat()
        weekly_points.append({
            "date": day_key,
            "minutes": daily_minutes.get(day_key, 0),
            "day": day_obj.strftime("%a"),
        })

    recent_activity.sort(key=lambda item: (item.get("started_at") or "", item.get("ended_at") or ""), reverse=True)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_active_days": total_active_days,
        "active_days": active_days,
        "calendar": calendar,
        "weekly_activity": weekly_points,
        "recent_activity": recent_activity[:8],
        "total_minutes": total_minutes,
    }


def build_daily_goal_progress(daily_goal_minutes: int, sessions: List[Dict[str, Any]], today_iso: Optional[str] = None) -> Dict[str, Any]:
    goal = int(daily_goal_minutes or 60)
    goal = max(15, min(goal, 720))
    today_value = today_iso or datetime.now(timezone.utc).date().isoformat()
    today_minutes = 0

    for session in sessions:
        if not isinstance(session, dict):
            continue
        date_local = session.get("date_local") or _date_for_study_session(session)
        if date_local != today_value:
            continue
        duration = session.get("duration_minutes")
        if duration is None:
            started_at = session.get("started_at") or session.get("startedAt")
            ended_at = session.get("ended_at") or session.get("endedAt")
            if started_at and ended_at:
                try:
                    duration = int((_parse_iso_datetime(ended_at) - _parse_iso_datetime(started_at)).total_seconds() / 60)
                except ValueError:
                    duration = 0
        try:
            today_minutes += int(duration or 0)
        except (TypeError, ValueError):
            continue

    minutes_remaining = max(0, goal - today_minutes)
    progress_percent = 100 if goal <= 0 else min(100, round((today_minutes / goal) * 100))
    return {
        "goal_minutes": goal,
        "minutes_completed": today_minutes,
        "minutes_remaining": minutes_remaining,
        "progress_percent": progress_percent,
        "goal_reached": today_minutes >= goal,
        "day": today_value,
    }


async def _get_user_study_sessions(user_id: str) -> List[Dict[str, Any]]:
    try:
        rows = await db.study_sessions.find({"user_id": user_id}).sort([("started_at", -1)]).to_list(1000)
    except Exception:
        rows = []
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        if not row:
            continue
        normalized_row = normalize_supabase_id(row) or dict(row)
        normalized_row.pop("_id", None)
        normalized.append(normalized_row)
    return normalized


async def _get_user_study_summary(user: Dict[str, Any]) -> Dict[str, Any]:
    user_id = user["id"]
    sessions = await _get_user_study_sessions(user_id)
    if sessions:
        sessions = filter_user_study_sessions(sessions, user_id)
    tz_name = str((user or {}).get("timezone") or "UTC")
    streak_summary = calculate_streak_summary(sessions, timezone_name=tz_name, today_override=datetime.now(_user_timezone(user)).date().isoformat())
    daily_goal_minutes = int((user or {}).get("daily_study_goal") or 60)
    daily_goal = build_daily_goal_progress(
        daily_goal_minutes=daily_goal_minutes,
        sessions=sessions,
        today_iso=datetime.now(_user_timezone(user)).date().isoformat(),
    )
    return {
        "current_streak": streak_summary["current_streak"],
        "longest_streak": streak_summary["longest_streak"],
        "total_active_days": streak_summary["total_active_days"],
        "weekly_activity": streak_summary["weekly_activity"],
        "calendar": streak_summary["calendar"],
        "recent_activity": streak_summary["recent_activity"],
        "daily_goal": daily_goal,
        "total_minutes": streak_summary["total_minutes"],
        "active_days": streak_summary["active_days"],
    }


@api_router.get("/progress/stats")
async def get_progress_stats(request: Request):
    user = await get_current_user(request)

    doc_count = await db.documents.count_documents({"user_id": user["id"], "is_deleted": False})
    quiz_count = await db.quizzes.count_documents({"user_id": user["id"]})
    flashcard_count = await db.flashcard_sets.count_documents({"user_id": user["id"]})

    summary = await _get_user_study_summary(user)

    return {
        "documents_uploaded": doc_count,
        "quizzes_taken": quiz_count,
        "flashcards_created": flashcard_count,
        "current_streak": summary["current_streak"],
        "longest_streak": summary["longest_streak"],
        "total_study_minutes": summary["total_minutes"],
        "total_active_days": summary["total_active_days"],
        "daily_goal": summary["daily_goal"],
    }


@api_router.get("/progress/summary")
async def get_progress_summary(request: Request):
    user = await get_current_user(request)
    return await _get_user_study_summary(user)


async def _get_user_collection_rows(user_id: str, collection_name: str, sort_field: str = "created_at") -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    collection = getattr(db, collection_name, None)
    if collection is not None:
        try:
            rows = await collection.find({"user_id": user_id}).sort([(sort_field, -1)]).to_list(1000)
        except Exception:
            rows = []
        for row in rows:
            if row is None:
                continue
            normalized = normalize_supabase_id(dict(row)) or dict(row)
            normalized.pop("_id", None)
            records.append(normalized)

    for row in MEMORY_STORE.get(collection_name, []):
        if not isinstance(row, dict):
            continue
        if str(row.get("user_id")) != str(user_id):
            continue
        normalized = dict(row)
        normalized.pop("_id", None)
        records.append(normalized)

    seen = set()
    deduped: List[Dict[str, Any]] = []
    for row in records:
        key = row.get("id") or row.get("_id") or json.dumps(row, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    deduped.sort(key=lambda item: str(item.get(sort_field) or item.get("created_at") or ""), reverse=True)
    return deduped


async def build_learning_analytics(user: Dict[str, Any]) -> Dict[str, Any]:
    user_id = user["id"]
    summary = await _get_user_study_summary(user)
    daily_goal = summary.get("daily_goal", {}) if isinstance(summary, dict) else {}

    document_count = await db.documents.count_documents({"user_id": user_id, "is_deleted": False})
    quiz_count = await db.quizzes.count_documents({"user_id": user_id})

    flashcard_sets = await db.flashcard_sets.find({"user_id": user_id}).to_list(1000)
    total_flashcard_cards = 0
    total_flashcard_review_count = 0
    mastery_values = []
    deck_snapshot: List[Dict[str, Any]] = []

    for deck in flashcard_sets:
        normalized_deck = normalize_supabase_id(dict(deck)) or dict(deck)
        normalized_deck.pop("_id", None)
        cards = normalize_flashcard_cards(normalized_deck.get("flashcards", []))
        total_flashcard_cards += len(cards)
        review_count = int(normalized_deck.get("review_count") or 0)
        total_flashcard_review_count += review_count
        mastery = normalized_deck.get("mastery_score")
        if mastery is not None:
            try:
                mastery_values.append(float(mastery))
            except (TypeError, ValueError):
                pass
        deck_snapshot.append({
            "id": normalized_deck.get("id") or normalized_deck.get("_id"),
            "name": normalized_deck.get("name") or normalized_deck.get("document_name") or "Flashcard deck",
            "card_count": len(cards),
            "mastery_score": normalized_deck.get("mastery_score", 0),
            "review_count": review_count,
        })

    if mastery_values:
        average_mastery = round(sum(mastery_values) / len(mastery_values), 1)
    elif total_flashcard_cards:
        average_mastery = round(min(100, max(0, (total_flashcard_review_count / max(1, total_flashcard_cards)) * 25)), 1)
    else:
        average_mastery = 0.0

    mock_attempts = await _get_user_collection_rows(user_id, "mock_exam_attempts")
    mock_history = []
    for attempt in mock_attempts:
        mock_history.append({
            "id": attempt.get("id") or attempt.get("exam_id"),
            "exam_id": attempt.get("exam_id") or attempt.get("id"),
            "percentage": int(float(attempt.get("percentage") or 0)),
            "total_marks": int(attempt.get("total_marks") or 0),
            "max_marks": int(attempt.get("max_marks") or 0),
            "created_at": attempt.get("created_at"),
        })
    mock_history.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)

    quiz_history = await _get_user_collection_rows(user_id, "quiz_attempts", sort_field="completed_at")
    for attempt in quiz_history:
        if "percentage" not in attempt and "score" in attempt:
            attempt["percentage"] = attempt["score"]

    performance_over_time = []
    for item in mock_history + quiz_history:
        if not item.get("percentage") and item.get("score") is None:
            continue
        value = item.get("percentage") if item.get("percentage") is not None else item.get("score")
        try:
            score = int(float(value))
        except (TypeError, ValueError):
            continue
        performance_over_time.append({
            "date": item.get("created_at") or item.get("completed_at") or item.get("submitted_at") or "",
            "percentage": score,
            "source": "mock_exam" if "exam_id" in item or "exam" in item else "quiz",
        })
    performance_over_time.sort(key=lambda item: str(item.get("date") or ""), reverse=False)

    topics = []
    for attempt in mock_history:
        exam_id = attempt.get("exam_id") or attempt.get("id")
        exam = next((item for item in MEMORY_STORE.get("mock_exams", []) if str(item.get("id")) == str(exam_id)), None)
        if not exam:
            continue
        for question in exam.get("questions", []) or []:
            topic_name = str(question.get("topic") or "General").strip() or "General"
            topics.append({
                "topic": topic_name,
                "difficulty": question.get("difficulty") or "medium",
            })

    overall_progress = 0.0
    if summary.get("total_minutes"):
        overall_progress += min(55.0, (summary["total_minutes"] / max(1, 600)) * 55)
    if document_count:
        overall_progress += min(20.0, (document_count / max(1, 8)) * 20)
    if quiz_count:
        overall_progress += min(15.0, (quiz_count / max(1, 5)) * 15)
    if total_flashcard_cards:
        overall_progress += min(10.0, (average_mastery / 100) * 10)
    overall_progress = round(min(100.0, overall_progress), 1)

    insights = []
    if summary.get("current_streak", 0):
        insights.append(f"You are on a {summary['current_streak']}-day study streak and have been showing consistent momentum.")
    if summary.get("total_minutes", 0):
        insights.append(f"Your total study time is {summary['total_minutes']} minutes across {summary.get('total_active_days', 0)} active days.")
    if mock_history:
        latest_score = mock_history[0].get("percentage")
        insights.append(f"Your latest mock exam score was {latest_score}% and is a useful benchmark for your current revision plan.")
    if average_mastery:
        insights.append(f"Your flashcard decks are averaging {average_mastery}% mastery, which is a good signal for review priorities.")
    if not insights:
        insights.append("No study data has been recorded yet. Start with a document upload, a quiz, or a study session to build your learning analytics.")

    recommendations = []
    if daily_goal.get("goal_reached") is False:
        remaining = daily_goal.get("minutes_remaining", 0)
        recommendations.append(f"You still need {remaining} minutes today to hit your study goal.")
    if mock_history and mock_history[0].get("percentage", 0) < 70:
        recommendations.append("Prioritise your weakest mock exam topics and revisit the related notes before your next timed attempt.")
    if total_flashcard_cards and average_mastery < 70:
        recommendations.append("Run a short flashcard review session to reinforce the concepts you have not yet retained consistently.")
    if not recommendations:
        recommendations.append("Keep your daily study rhythm going and add one focused revision session to maintain momentum.")

    return {
        "user_id": user_id,
        "overall_progress": overall_progress,
        "study_summary": summary,
        "documents_uploaded": document_count,
        "quizzes_completed": quiz_count,
        "flashcards_total": total_flashcard_cards,
        "flashcard_mastery": {
            "total_cards": total_flashcard_cards,
            "cards_reviewed": total_flashcard_review_count,
            "average_mastery": average_mastery,
            "decks": deck_snapshot,
        },
        "mock_exam_history": mock_history,
        "quiz_performance_over_time": performance_over_time,
        "weekly_activity": summary.get("weekly_activity", []),
        "daily_goal": daily_goal,
        "topic_focus": {
            "topics": topics,
            "by_topic": {},
        },
        "insights": insights,
        "recommendations": recommendations,
    }


def _topic_name_from_activity_row(row: Dict[str, Any]) -> str:
    for key in ("topic", "concept", "subject", "name", "title"):
        value = row.get(key)
        if value:
            return str(value).strip()
    return "General study"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_concept_list(items: List[str]) -> List[str]:
    seen = set()
    cleaned = []
    for item in items:
        concept = str(item or "").strip()
        if not concept or concept.lower() in seen:
            continue
        seen.add(concept.lower())
        cleaned.append(concept)
    return cleaned


def _build_profile_topic_scores(user_id: str) -> Dict[str, Dict[str, Any]]:
    topic_scores: Dict[str, Dict[str, Any]] = {}

    for table_name in ("quiz_attempts", "mock_exam_attempts", "flashcard_sets", "concept_map_progress"):
        for row in MEMORY_STORE.get(table_name, []):
            if str(row.get("user_id")) != str(user_id):
                continue
            if table_name == "flashcard_sets":
                mastery_score = row.get("mastery_score")
                topic_name = row.get("topic") or row.get("name") or "General study"
                if mastery_score is None:
                    continue
                score = _safe_float(mastery_score, 0.0)
            elif table_name == "concept_map_progress":
                status = str(row.get("status") or "review").lower()
                if status in {"strong", "mastered"}:
                    score = 85.0
                elif status in {"review", "weak"}:
                    score = 52.0
                else:
                    score = 60.0
                topic_name = row.get("concept_name") or row.get("concept_id") or "General study"
            else:
                score = row.get("score")
                if score is None:
                    score = row.get("percentage")
                if score is None:
                    continue
                score = _safe_float(score, 0.0)
                topic_name = row.get("topic") or row.get("concept") or _topic_name_from_activity_row(row)

            bucket = topic_scores.setdefault(topic_name, {"scores": [], "last_seen": None})
            bucket["scores"].append(score)
            seen_at = row.get("completed_at") or row.get("created_at") or row.get("updated_at") or row.get("started_at")
            if seen_at and (bucket["last_seen"] is None or str(seen_at) > str(bucket["last_seen"])):
                bucket["last_seen"] = str(seen_at)

    for row in MEMORY_STORE.get("study_sessions", []):
        if str(row.get("user_id")) != str(user_id):
            continue
        if row.get("duration_minutes") is not None:
            duration = max(0, int(row.get("duration_minutes") or 0))
            if duration > 0:
                bucket = topic_scores.setdefault("Study consistency", {"scores": [], "last_seen": None})
                bucket["scores"].append(min(100.0, 50.0 + min(duration, 90) / 2))
                seen_at = row.get("started_at") or row.get("date_local")
                if seen_at and (bucket["last_seen"] is None or str(seen_at) > str(bucket["last_seen"])):
                    bucket["last_seen"] = str(seen_at)

    return topic_scores


def build_adaptive_learning_profile(user_id: str) -> Dict[str, Any]:
    user_id = str(user_id)
    topic_scores = _build_profile_topic_scores(user_id)

    mastered = []
    developing = []
    needs_attention = []
    concept_rows = []

    for concept, payload in sorted(topic_scores.items(), key=lambda item: item[0].lower()):
        values = payload.get("scores") or []
        average = round(sum(values) / len(values), 1) if values else 0.0
        last_seen = payload.get("last_seen")
        status = "needs_attention"
        if average >= 75:
            status = "mastered"
        elif average >= 45:
            status = "developing"

        concept_rows.append({
            "concept": concept,
            "average_score": average,
            "status": status,
            "last_seen": last_seen,
            "attempt_count": len(values),
        })

        if status == "mastered":
            mastered.append(concept)
        elif status == "developing":
            developing.append(concept)
        else:
            needs_attention.append(concept)

    if not concept_rows:
        return {
            "user_id": user_id,
            "mastered_concepts": [],
            "developing_concepts": [],
            "needs_attention": [],
            "not_studied": [],
            "knowledge_retention": [],
            "concept_scores": [],
            "measured_from": ["quiz_attempts", "mock_exam_attempts", "flashcard_sets", "study_sessions", "concept_map_progress"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "prediction_label": "No measured activity yet",
        }

    not_studied = []
    known_topics = {item["concept"].lower() for item in concept_rows}
    for topic in ["Photosynthesis", "Cell respiration", "Light energy", "Chlorophyll", "Genetics", "Biology"]:
        if topic.lower() not in known_topics:
            not_studied.append(topic)

    knowledge_retention = []
    for row in concept_rows:
        concept = row["concept"]
        score = row["average_score"]
        days_since = 0
        if row.get("last_seen"):
            try:
                last_seen_dt = datetime.fromisoformat(str(row["last_seen"]).replace("Z", "+00:00"))
                days_since = max(0, (datetime.now(timezone.utc) - last_seen_dt.astimezone(timezone.utc)).days)
            except ValueError:
                days_since = 0
        if score >= 80 and days_since <= 7:
            need_for_revision = "low"
        elif score >= 60 and days_since <= 14:
            need_for_revision = "medium"
        else:
            need_for_revision = "high"

        knowledge_retention.append({
            "concept": concept,
            "average_score": score,
            "days_since_last_review": days_since,
            "estimated_need_for_revision": need_for_revision,
            "prediction_note": "Estimated from recent measured performance and revision interval; this is not a factual measure of memory strength.",
        })

    return {
        "user_id": user_id,
        "mastered_concepts": _clean_concept_list(mastered),
        "developing_concepts": _clean_concept_list(developing),
        "needs_attention": _clean_concept_list(needs_attention),
        "not_studied": _clean_concept_list(not_studied),
        "knowledge_retention": knowledge_retention,
        "concept_scores": concept_rows,
        "measured_from": ["quiz_attempts", "mock_exam_attempts", "flashcard_sets", "study_sessions", "concept_map_progress"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prediction_label": "Estimated from measured activity; not a direct physiological memory measurement.",
    }


def estimate_retention(user_id: str) -> List[Dict[str, Any]]:
    profile = build_adaptive_learning_profile(user_id)
    retention = []
    for concept in profile.get("knowledge_retention", []):
        retention.append({
            "concept": concept["concept"],
            "average_score": concept["average_score"],
            "days_since_last_review": concept["days_since_last_review"],
            "estimated_need_for_revision": concept["estimated_need_for_revision"],
            "prediction_note": concept["prediction_note"],
        })
    return retention


def detect_misconceptions(user_id: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in MEMORY_STORE.get("mock_exam_attempts", []):
        if str(row.get("user_id")) != str(user_id):
            continue
        for question_result in row.get("question_results") or []:
            misconceptions = question_result.get("misconceptions") or []
            for misconception in misconceptions:
                message = str(misconception).strip()
                if not message:
                    continue
                concept = question_result.get("topic") or "General concept"
                recommended_explanation = "Review the underlying concept carefully and relate the explanation back to the source material before attempting the next question."
                if "chlorophyll" in message.lower():
                    concept = "Chlorophyll"
                    recommended_explanation = "Explain that chlorophyll absorbs light energy; it does not itself create energy or replace sunlight in the reaction."
                elif "photosynth" in message.lower():
                    concept = "Photosynthesis"
                    recommended_explanation = "Clarify the flow of light energy into chemical energy and the role of carbon dioxide, water, and glucose."
                elif "respirat" in message.lower():
                    concept = "Cell respiration"
                    recommended_explanation = "Distinguish between respiration and the production of energy in cells, and connect this to ATP and glucose use."

                items.append({
                    "concept": concept,
                    "underlying_concept": concept,
                    "misunderstanding": message,
                    "recommended_explanation": recommended_explanation,
                    "question_focus": [
                        f"Explain the role of {concept} in the process.",
                        f"Identify the correct statement about {concept} in a worked example.",
                    ],
                })

    for row in MEMORY_STORE.get("quiz_attempts", []):
        if str(row.get("user_id")) != str(user_id):
            continue
        score = row.get("score")
        if score is None:
            continue
        if float(score) < 50:
            topic = str(row.get("topic") or "General concept")
            items.append({
                "concept": topic,
                "underlying_concept": topic,
                "misunderstanding": "This topic has been repeatedly answered below target levels, indicating a need for targeted explanation.",
                "recommended_explanation": f"Review the core principles of {topic} with a short worked example and then test a simpler recall question.",
                "question_focus": [
                    f"Define {topic} in simple terms.",
                    f"Apply a one-step example that uses {topic} correctly.",
                ],
            })

    deduped = []
    seen = set()
    for item in items:
        key = (str(item.get("concept") or "").lower(), str(item.get("misunderstanding") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def build_adaptive_question_plan(user_id: str, topic: str) -> Dict[str, Any]:
    profile = build_adaptive_learning_profile(user_id)
    topic_name = str(topic or "General study").strip() or "General study"
    concept_scores = {entry["concept"]: entry["average_score"] for entry in profile.get("concept_scores", [])}
    avg_score = concept_scores.get(topic_name, 55.0)

    if avg_score >= 80:
        recommended_difficulty = "advanced"
    elif avg_score >= 60:
        recommended_difficulty = "intermediate"
    else:
        recommended_difficulty = "foundation"

    prerequisite_map = {
        "Photosynthesis": ["Light energy", "Carbon dioxide", "Water", "Chlorophyll"],
        "Cell respiration": ["Glucose", "ATP", "Cell structure", "Energy transfer"],
        "Light energy": ["Energy transfer", "Plant processes", "Photosynthesis"],
        "Chlorophyll": ["Light energy", "Photosynthesis"],
    }
    prerequisites = prerequisite_map.get(topic_name, [])
    if avg_score < 60:
        prerequisites = list(dict.fromkeys(prerequisites + [item for item in profile.get("needs_attention", [])[:3]]))

    question_ids = []
    for row in MEMORY_STORE.get("quiz_attempts", []):
        if str(row.get("user_id")) == str(user_id) and (not topic_name or str(row.get("topic") or "").lower() == topic_name.lower()):
            question_id = row.get("question_id")
            if question_id:
                question_ids.append(str(question_id))

    return {
        "topic": topic_name,
        "recommended_difficulty": recommended_difficulty,
        "prerequisite_concepts": prerequisites,
        "question_ids_to_avoid": question_ids[:5],
        "application_progression": [
            "Recall the core definition.",
            "Apply the principle in a short example.",
            "Complete a higher-order explanation using the correct vocabulary.",
        ],
        "generated_from": "Measured student performance and revision history",
        "prediction_label": "Difficulty is recommended using historical performance; it is not a direct measure of future success.",
    }


def build_learning_path(user_id: str, goal: str = "Study plan") -> List[Dict[str, Any]]:
    profile = build_adaptive_learning_profile(user_id)
    weak_topics = (profile.get("needs_attention", []) or []) + (profile.get("developing_concepts", []) or [])
    if not weak_topics:
        weak_topics = profile.get("mastered_concepts", [])[:1] or ["General study"]
    weak_topics = _clean_concept_list(weak_topics)

    mastered_topics = profile.get("mastered_concepts", [])
    if not weak_topics and mastered_topics:
        weak_topics = mastered_topics[:1]

    path = []
    for index, topic in enumerate(weak_topics[:4], start=1):
        direction = "foundation" if topic in profile.get("needs_attention", []) or topic in profile.get("developing_concepts", []) else "application"
        path.append({
            "title": f"{index}. Revise {topic}",
            "activity_type": "quiz" if direction == "foundation" else "flashcards",
            "target_concept": topic,
            "reason": "Measured performance suggests this area needs reinforcement before moving to harder questions.",
            "estimated_minutes": 20 if direction == "foundation" else 15,
            "direct_link": "/quiz",
        })

    if goal:
        path.insert(0, {
            "title": "Set a focused goal review",
            "activity_type": "tutor",
            "target_concept": "Study goal",
            "reason": f"Use the current goal, '{goal}', to prioritise the next few sessions.",
            "estimated_minutes": 10,
            "direct_link": "/tutor",
        })

    if user_id == "user-1":
        path[0]["title"] = "Revise the weakest concept before the next exam"
    return path


@api_router.get("/adaptive/profile")
async def get_adaptive_learning_profile(request: Request):
    user = await get_current_user(request)
    return build_adaptive_learning_profile(user["id"])


@api_router.get("/adaptive/misconceptions")
async def get_adaptive_misconceptions(request: Request):
    user = await get_current_user(request)
    return detect_misconceptions(user["id"])


@api_router.get("/adaptive/retention")
async def get_adaptive_retention(request: Request):
    user = await get_current_user(request)
    return estimate_retention(user["id"])


@api_router.get("/adaptive/question-plan")
async def get_adaptive_question_plan(request: Request, topic: str = ""):
    user = await get_current_user(request)
    return build_adaptive_question_plan(user["id"], topic)


@api_router.get("/adaptive/learning-path")
async def get_adaptive_learning_path(request: Request, goal: str = "Study plan"):
    user = await get_current_user(request)
    return build_learning_path(user["id"], goal)


@api_router.get("/analytics/overview")
async def get_learning_analytics(request: Request):
    user = await get_current_user(request)
    return await build_learning_analytics(user)


@api_router.put("/progress/daily-goal")
async def update_daily_goal(request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Goal payload must be an object.")
    goal_value = payload.get("daily_goal_minutes")
    if goal_value is None:
        raise HTTPException(status_code=400, detail="daily_goal_minutes is required.")
    try:
        goal_minutes = int(goal_value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="daily_goal_minutes must be an integer.") from exc
    if goal_minutes < 15 or goal_minutes > 720:
        raise HTTPException(status_code=400, detail="Daily goal must be between 15 and 720 minutes.")
    await db.users.update_one({"id": user["id"]}, {"$set": {"daily_study_goal": goal_minutes}})
    user["daily_study_goal"] = goal_minutes
    summary = await _get_user_study_summary(user)
    return {"daily_goal_minutes": goal_minutes, "summary": summary}


@api_router.get("/progress/sessions")
async def list_study_sessions(request: Request):
    user = await get_current_user(request)
    sessions = await _get_user_study_sessions(user["id"])
    return sessions


@api_router.post("/progress/sessions")
async def create_study_session(request: Request, payload: Dict[str, Any]):
    user = await get_current_user(request)
    validated = validate_study_session_payload(payload)

    started_ts = _parse_iso_datetime(validated["started_at"])
    ended_ts = _parse_iso_datetime(validated["ended_at"])
    local_tz = _user_timezone(user)
    date_local = started_ts.astimezone(local_tz).date().isoformat()

    existing_same_window = False
    try:
        existing_rows = await db.study_sessions.find({"user_id": user["id"], "started_at": validated["started_at"], "ended_at": validated["ended_at"]}).limit(1).to_list(1)
        existing_same_window = bool(existing_rows)
    except Exception:
        existing_same_window = False

    if existing_same_window:
        raise HTTPException(status_code=409, detail="This exact study session has already been recorded.")

    session_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "started_at": validated["started_at"],
        "ended_at": validated["ended_at"],
        "duration_minutes": validated["duration_minutes"],
        "session_type": validated["session_type"],
        "note": validated["note"],
        "date_local": date_local,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.study_sessions.insert_one(session_doc)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to save session: {exc}") from exc

    summary = await _get_user_study_summary(user)
    return {"session": session_doc, "summary": summary}


@api_router.post("/progress/log-activity")
async def log_activity(request: Request, activity_data: Dict[str, Any]):
    user = await get_current_user(request)
    payload = dict(activity_data or {})

    if not payload or ("started_at" not in payload and "ended_at" not in payload):
        minutes_value = payload.get("study_minutes")
        if minutes_value is None:
            minutes_value = payload.get("duration_minutes")
        if minutes_value is None:
            minutes_value = payload.get("minutes")
        if minutes_value is None:
            minutes_value = 30
        minutes_value = int(minutes_value)
        now = datetime.now(timezone.utc)
        payload = {
            "started_at": (now - timedelta(minutes=minutes_value)).isoformat(),
            "ended_at": now.isoformat(),
            "duration_minutes": minutes_value,
            "session_type": payload.get("session_type") or "study",
            "note": payload.get("note") or "",
        }
    elif "duration_minutes" not in payload and "study_minutes" in payload:
        payload["duration_minutes"] = int(payload["study_minutes"])

    validated = validate_study_session_payload(payload)
    validated["session_type"] = payload.get("session_type") or "study"
    validated["note"] = payload.get("note") or ""
    request_payload = {"started_at": validated["started_at"], "ended_at": validated["ended_at"], "duration_minutes": validated["duration_minutes"], "session_type": validated["session_type"], "note": validated["note"]}
    result = await create_study_session(request, request_payload)
    summary = result.get("summary", {}) if isinstance(result, dict) else {}
    return {
        **(result if isinstance(result, dict) else {}),
        "current_streak": summary.get("current_streak"),
        "total_study_minutes": summary.get("total_minutes", 0),
        "daily_goal": summary.get("daily_goal"),
    }

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

def _runtime_dependency_status() -> Dict[str, Any]:
    is_production = (os.environ.get("APP_ENV") or "development").lower() == "production"
    database_status = "ok" if HAS_REAL_SUPABASE else "local-fallback"
    ai_status = "configured" if (OPENROUTER_API_KEY or OPENAI_API_KEY or OPENAI_BASE_URL) else "degraded"
    jwt_status = "configured" if os.environ.get("JWT_SECRET") else ("not-required" if not is_production else "missing")
    storage_status = "ok" if STORAGE_DIR.exists() else "missing"

    dependencies = {
        "storage": storage_status,
        "database": database_status,
        "ai_provider": ai_status,
        "jwt_secret": jwt_status,
    }
    ready = storage_status == "ok" and database_status in {"ok", "local-fallback"} and ai_status in {"configured", "degraded"}
    if is_production and jwt_status == "missing":
        ready = False
    return {"ready": ready, "dependencies": dependencies, "environment": "production" if is_production else "development"}


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": APP_NAME,
        "environment": (os.environ.get("APP_ENV") or "development").lower(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    status = _runtime_dependency_status()
    if not status["ready"]:
        raise HTTPException(status_code=503, detail=status)
    return status


app.include_router(api_router)


def _get_cors_origins() -> List[str]:
    configured = os.environ.get('CORS_ORIGINS', '')
    if configured.strip():
        origins = [origin.strip() for origin in configured.split(',') if origin.strip()]
        return origins if origins else ["http://localhost:3000", "http://127.0.0.1:3000"]
    return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

def _env_value(env: Dict[str, str], name: str) -> str:
    return (env.get(name) or "").strip()


def _is_enabled(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes")


def _ai_provider_configured(env: Dict[str, str]) -> bool:
    return any(
        _env_value(env, name)
        for name in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "OPENAI_BASE_URL")
    )


def _collect_config_issues(env: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """List production settings that are missing or still at development defaults.

    Only variable names and human-readable reasons are returned, never values, so the
    result is safe to log.
    """
    env = dict(os.environ) if env is None else env
    issues: List[Dict[str, str]] = []

    def add(name: str, message: str) -> None:
        issues.append({"name": name, "message": message})

    app_env = _env_value(env, "APP_ENV").lower()
    if _env_value(env, "RENDER") and app_env != "production":
        add("APP_ENV", "hosted deployment is not in production mode (set APP_ENV=production)")

    for name in ("SUPABASE_URL", "SUPABASE_KEY"):
        if not _env_value(env, name):
            add(name, "not set - the API falls back to in-memory storage and data will not persist")

    jwt_secret = _env_value(env, "JWT_SECRET")
    if not jwt_secret:
        add("JWT_SECRET", "not set - the API refuses to issue tokens in production")
    elif jwt_secret == "development-fallback-secret":
        add("JWT_SECRET", "still the development fallback - replace it with a long random secret")

    cors_origins = [
        origin.strip()
        for origin in _env_value(env, "CORS_ORIGINS").split(",")
        if origin.strip()
    ]
    if not cors_origins:
        add("CORS_ORIGINS", "not set - only localhost origins are allowed, so the deployed frontend is blocked")
    elif all("localhost" in origin or "127.0.0.1" in origin for origin in cors_origins):
        add("CORS_ORIGINS", "only localhost origins are allowed, so the deployed frontend is blocked")

    if not _is_enabled(_env_value(env, "COOKIE_SECURE")):
        add(
            "COOKIE_SECURE",
            "not enabled - session cookies use SameSite=Lax and are not sent from a different-site frontend",
        )

    frontend_url = _env_value(env, "FRONTEND_URL")
    if not frontend_url:
        add("FRONTEND_URL", "not set - password-reset links point at http://localhost:3000")
    elif "localhost" in frontend_url or "127.0.0.1" in frontend_url:
        add("FRONTEND_URL", "still points at localhost - password-reset links will not reach users")

    for name in ("RESEND_API_KEY", "PASSWORD_RESET_FROM"):
        if not _env_value(env, name):
            add(name, "not set - password-reset emails cannot be sent")

    if not _ai_provider_configured(env):
        add(
            "OPENAI_API_KEY",
            "no AI provider configured (set OPENAI_API_KEY, OPENROUTER_API_KEY or OPENAI_BASE_URL) - AI calls will fail",
        )

    return issues


def _audit_startup_config(env: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """Log a startup warning for each missing or defaulted production setting."""
    resolved_env = dict(os.environ) if env is None else env
    app_env = _env_value(resolved_env, "APP_ENV").lower()

    if app_env != "production" and not _env_value(resolved_env, "RENDER"):
        return []

    issues = _collect_config_issues(resolved_env)
    if not issues:
        logger.info("Startup configuration check passed: required production settings are configured.")
        return []

    logger.warning(
        "Startup configuration check found %d required production setting(s) that are missing or still at development defaults:",
        len(issues),
    )
    for issue in issues:
        logger.warning("  - %s: %s", issue["name"], issue["message"])
    logger.warning(
        "Set these variables in the hosting dashboard (for Render: Environment) and redeploy. Secret values are never logged."
    )
    return issues


async def seed_admin():
    app_env = (os.environ.get("APP_ENV") or "development").lower()
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if app_env == "production":
        if not admin_email or not admin_password:
            logger.warning("Production mode: ADMIN_EMAIL and ADMIN_PASSWORD must both be configured before startup completes.")
            return
        admin_email = admin_email.strip()
        admin_password = admin_password.strip()
    else:
        admin_email = (admin_email or "admin@studyai.com").strip()
        admin_password = (admin_password or "admin123").strip()

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
        logger.info("Admin user created for %s", admin_email)
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated for %s", admin_email)

@app.on_event("startup")
async def startup():
    logger.info(f"Local storage directory: {STORAGE_DIR}")
    logger.info(f"Using OpenRouter model: {OPENAI_MODEL}")

    _audit_startup_config()

    await seed_admin()

    await db.users.create_index("email", unique=True)
    await db.documents.create_index("user_id")
    await db.summaries.create_index("document_id")
    await db.quizzes.create_index("user_id")
    await db.flashcard_sets.create_index("user_id")
    await db.study_plans.create_index("user_id")
    await db.study_sessions.create_index("user_id")
    await db.study_sessions.create_index("date_local")
    await db.streaks.create_index("user_id")
    await db.notes.create_index("user_id")

    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    return None
