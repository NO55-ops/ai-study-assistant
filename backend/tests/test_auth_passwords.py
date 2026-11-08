import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, Response

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SEND_PASSWORD_RESET_EMAIL", "0")

import server
from server import (
    LoginRequest,
    RegisterRequest,
    MEMORY_STORE,
    confirm_password_reset,
    hash_password,
    login,
    register,
    request_password_reset,
    verify_password,
)


@pytest.fixture(autouse=True)
def clear_memory_store():
    previous_supabase = server.supabase
    server.supabase = server.MemorySupabaseClient()
    MEMORY_STORE.clear()
    yield
    MEMORY_STORE.clear()
    server.supabase = previous_supabase


def test_correct_password_with_valid_bcrypt_hash():
    password = "valid-password-123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_incorrect_password_with_valid_bcrypt_hash():
    password = "correct-password"
    hashed = hash_password(password)

    assert verify_password("wrong-password", hashed) is False


def test_missing_password_hash_returns_false():
    assert verify_password("any-password", "") is False
    assert verify_password("any-password", None) is False


def test_malformed_password_hash_returns_false_instead_of_raising():
    assert verify_password("any-password", "not-a-valid-bcrypt-hash") is False


def test_registration_then_successful_login():
    email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "pw123456"

    register_response = Response()
    created_user = asyncio.run(
        register(
            RegisterRequest(email=email, password=password, name="Test User"),
            register_response,
        )
    )

    assert created_user["email"] == email.lower()
    assert "password_hash" not in created_user

    login_response = Response()
    session_user = asyncio.run(
        login(
            LoginRequest(email=email, password=password),
            login_response,
        )
    )

    assert session_user["email"] == email.lower()
    assert "password_hash" not in session_user


def test_password_reset_request_and_confirmation_flow(monkeypatch):
    email = f"reset_user_{uuid.uuid4().hex[:8]}@example.com"
    original_password = "pw123456"
    new_password = "newPassword456!"
    reset_token = "fixed-reset-token-123"
    monkeypatch.setattr(server.secrets, "token_urlsafe", lambda *_args, **_kwargs: reset_token)

    register_response = Response()
    asyncio.run(
        register(
            RegisterRequest(email=email, password=original_password, name="Reset User"),
            register_response,
        )
    )

    request_response = asyncio.run(
        request_password_reset({"email": email})
    )

    assert "debug_reset_token" not in request_response
    assert request_response["message"] == "If an account exists for this email, a password reset link was sent."

    confirm_response = asyncio.run(
        confirm_password_reset({
            "email": email,
            "token": reset_token,
            "new_password": new_password,
        })
    )

    assert confirm_response["message"] == "Password reset successfully"

    login_response = Response()
    session_user = asyncio.run(
        login(
            LoginRequest(email=email, password=new_password),
            login_response,
        )
    )

    assert session_user["email"] == email.lower()
    assert "password_hash" not in session_user


def test_password_reset_rejects_unknown_email_with_generic_message():
    response = asyncio.run(request_password_reset({"email": "missing@example.com"}))
    assert response == {"message": "If an account exists for this email, a password reset link was sent."}


def test_password_reset_rejects_expired_tokens(monkeypatch):
    email = f"expired_reset_{uuid.uuid4().hex[:8]}@example.com"
    asyncio.run(
        register(
            RegisterRequest(email=email, password="pw123456", name="Expired User"),
            Response(),
        )
    )

    token = "expired-reset-token"
    monkeypatch.setattr(server.secrets, "token_urlsafe", lambda *_args, **_kwargs: token)
    MEMORY_STORE.setdefault("password_reset_tokens", []).append({
        "id": str(uuid.uuid4()),
        "user_id": "unused-user-id",
        "email": email,
        "token_hash": server._password_reset_token_hash(token),
        "created_at": (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(),
        "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "used_at": None,
    })

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(confirm_password_reset({
            "email": email,
            "token": token,
            "new_password": "newPassword456!",
        }))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired reset token."


def test_password_reset_rejects_reused_token(monkeypatch):
    email = f"reuse_reset_{uuid.uuid4().hex[:8]}@example.com"
    reset_token = "reused-reset-token"
    monkeypatch.setattr(server.secrets, "token_urlsafe", lambda *_args, **_kwargs: reset_token)
    asyncio.run(
        register(
            RegisterRequest(email=email, password="pw123456", name="Reuse User"),
            Response(),
        )
    )

    request_response = asyncio.run(request_password_reset({"email": email}))
    assert "debug_reset_token" not in request_response

    first_confirm = asyncio.run(confirm_password_reset({
        "email": email,
        "token": reset_token,
        "new_password": "newPassword456!",
    }))
    assert first_confirm["message"] == "Password reset successfully"

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(confirm_password_reset({
            "email": email,
            "token": reset_token,
            "new_password": "anotherPassword123!",
        }))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired reset token."


def test_password_reset_rate_limits_repeated_requests(monkeypatch):
    email = f"rate_limited_{uuid.uuid4().hex[:8]}@example.com"
    reset_token = "rate-limit-token"
    monkeypatch.setattr(server.secrets, "token_urlsafe", lambda *_args, **_kwargs: reset_token)
    asyncio.run(
        register(
            RegisterRequest(email=email, password="pw123456", name="Rate User"),
            Response(),
        )
    )

    asyncio.run(request_password_reset({"email": email}))
    asyncio.run(request_password_reset({"email": email}))
    asyncio.run(request_password_reset({"email": email}))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(request_password_reset({"email": email}))

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many password reset requests. Please try again later."
