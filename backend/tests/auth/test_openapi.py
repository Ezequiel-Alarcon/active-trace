"""Strict TDD for the OpenAPI surface (C-03 §6)."""

from __future__ import annotations

import pytest

from app.main import app

pytestmark = pytest.mark.no_db


def test_login_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/login" in paths
    route = paths["/api/auth/login"]
    methods = getattr(route, "methods", set()) or set()
    assert "POST" in methods


def test_refresh_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/refresh" in paths


def test_logout_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/logout" in paths


def test_forgot_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/forgot" in paths


def test_reset_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/reset" in paths


def test_2fa_enroll_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/2fa/enroll" in paths


def test_2fa_verify_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/2fa/verify" in paths


def test_me_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/me" in paths


def test_session_endpoint_in_openapi() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/api/auth/session" in paths
    route = paths["/api/auth/session"]
    methods = getattr(route, "methods", set()) or set()
    assert "GET" in methods


def test_health_endpoint_preserved() -> None:
    paths = {r.path: r for r in app.routes}
    assert "/health" in paths
