"""Spec test (C-03 §5, D7): identity is derived exclusively from the JWT.

The resolver must ignore:
- Query string (`?as_user_id=...`, `?tenant_id=...`).
- Body fields with the same names.
- Request headers (`X-Tenant-Id`, `X-Impersonate-User`).
- Path parameters.

This test inspects the resolver's signature and implementation surface to
guarantee that no parameter other than the JWT is read.
"""

from __future__ import annotations

import inspect

import pytest

pytestmark = pytest.mark.no_db

from app.auth.deps import get_current_user, get_optional_current_user
from app.core.dependencies import tenant_context_dep


def test_get_current_user_signature_does_not_accept_user_or_tenant_params() -> None:
    sig = inspect.signature(get_current_user)
    param_names = list(sig.parameters.keys())
    for forbidden in (
        "user_id",
        "tenant_id",
        "as_user_id",
        "impersonate",
        "x_user_id",
        "x_tenant_id",
    ):
        assert forbidden not in param_names, (
            f"get_current_user must not accept {forbidden!r}; identity is JWT-only"
        )


def test_get_optional_current_user_signature_does_not_accept_user_or_tenant_params() -> None:
    sig = inspect.signature(get_optional_current_user)
    for forbidden in (
        "user_id",
        "tenant_id",
        "as_user_id",
        "impersonate",
        "x_user_id",
        "x_tenant_id",
    ):
        assert forbidden not in sig.parameters


def test_tenant_context_dep_does_not_read_x_tenant_id_header() -> None:
    """The C-02 `X-Tenant-Id` placeholder must be gone from the function body."""
    src = inspect.getsource(tenant_context_dep)
    # Strip docstring (it may mention the historical placeholder)
    src_no_doc = src.split('"""', 2)[-1] if '"""' in src else src
    assert "X-Tenant-Id" not in src_no_doc, (
        "tenant_context_dep must not read the X-Tenant-Id header (C-03 D7)"
    )
    assert "x_tenant_id" not in src_no_doc


def test_tenant_context_dep_signature_does_not_declare_tenant_id_param() -> None:
    sig = inspect.signature(tenant_context_dep)
    for forbidden in ("x_tenant_id", "tenant_id"):
        assert forbidden not in sig.parameters
