"""Tests for the production configuration startup audit."""

import logging

import server


COMPLETE_PRODUCTION_ENV = {
    "APP_ENV": "production",
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_KEY": "service-key",
    "JWT_SECRET": "a-long-random-production-secret",
    "CORS_ORIGINS": "https://study.example.app",
    "COOKIE_SECURE": "1",
    "FRONTEND_URL": "https://study.example.app",
    "RESEND_API_KEY": "re_test_key",
    "PASSWORD_RESET_FROM": "Study <noreply@example.app>",
    "OPENAI_API_KEY": "sk-test",
}


def _names(issues):
    return {issue["name"] for issue in issues}


def test_missing_production_settings_are_all_reported():
    issues = server._collect_config_issues({"APP_ENV": "production"})

    assert _names(issues) == {
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "JWT_SECRET",
        "CORS_ORIGINS",
        "COOKIE_SECURE",
        "FRONTEND_URL",
        "RESEND_API_KEY",
        "PASSWORD_RESET_FROM",
        "OPENAI_API_KEY",
    }
    assert all(issue["message"] for issue in issues)


def test_complete_production_config_reports_nothing():
    assert server._collect_config_issues(dict(COMPLETE_PRODUCTION_ENV)) == []


def test_development_defaults_are_flagged_in_production():
    env = dict(COMPLETE_PRODUCTION_ENV)
    env.update({
        "JWT_SECRET": "development-fallback-secret",
        "CORS_ORIGINS": "http://localhost:3000",
        "FRONTEND_URL": "http://localhost:3000",
        "COOKIE_SECURE": "0",
    })

    names = _names(server._collect_config_issues(env))

    assert {"JWT_SECRET", "CORS_ORIGINS", "FRONTEND_URL", "COOKIE_SECURE"} <= names


def test_audit_skips_non_production_without_hosting_signal(caplog):
    with caplog.at_level(logging.WARNING, logger=server.logger.name):
        issues = server._audit_startup_config({"APP_ENV": "development"})

    assert issues == []
    assert not [record for record in caplog.records if record.levelno >= logging.WARNING]


def test_audit_warns_in_hosted_deployment_even_without_app_env(caplog):
    with caplog.at_level(logging.WARNING, logger=server.logger.name):
        issues = server._audit_startup_config({"RENDER": "true"})

    assert issues
    assert "APP_ENV" in _names(issues)
    assert "missing or still at development defaults" in caplog.text


def test_audit_lists_names_and_never_logs_secret_values(caplog):
    env = dict(COMPLETE_PRODUCTION_ENV)
    env.update({
        "JWT_SECRET": "super-secret-jwt-value",
        "SUPABASE_KEY": "super-secret-service-key",
    })
    del env["RESEND_API_KEY"]

    with caplog.at_level(logging.WARNING, logger=server.logger.name):
        server._audit_startup_config(env)

    assert "RESEND_API_KEY" in caplog.text
    assert "super-secret-jwt-value" not in caplog.text
    assert "super-secret-service-key" not in caplog.text
