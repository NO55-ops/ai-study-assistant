import asyncio
import uuid

import pytest
from fastapi import Response

from server import (
    LoginRequest,
    RegisterRequest,
    MEMORY_STORE,
    hash_password,
    login,
    register,
    verify_password,
)


@pytest.fixture(autouse=True)
def clear_memory_store():
    MEMORY_STORE.clear()
    yield
    MEMORY_STORE.clear()


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
