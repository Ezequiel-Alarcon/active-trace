"""Strict TDD for app.auth.models (C-03 §2, D0, D2, D3).

Spec contract:
- `AuthUser` table `auth_user` with columns id, tenant_id, email_enc, password_hash,
  totp_secret_enc (nullable), totp_enabled (bool), is_active (bool),
  failed_login_count (int), last_login_at (datetime nullable), plus mixin columns.
- Indexes: (tenant_id, email_enc), (tenant_id, deleted_at).
- `AuthSession` table with jti UNIQUE, user_id FK ON DELETE CASCADE,
  rotated_to_id / replaced_by_id FKs ON DELETE SET NULL.
- `AuthPasswordReset` table with selector (8 chars) and unique index on `selector`.
"""

from __future__ import annotations


import pytest
import pytest_asyncio

from app.models.base import Base

pytestmark = [pytest.mark.no_db]


@pytest_asyncio.fixture
async def _models_in_metadata():
    """Import all auth models so they register on Base.metadata, then snapshot."""
    from app.auth import models  # noqa: F401
    from app.models import tenant  # noqa: F401  (FK target: tenant.id)

    yield


def test_auth_user_table_exists(_models_in_metadata) -> None:
    assert "auth_user" in Base.metadata.tables


def test_auth_user_columns(_models_in_metadata) -> None:
    cols = {c.name for c in Base.metadata.tables["auth_user"].columns}
    expected = {
        "id",
        "tenant_id",
        "email_enc",
        "password_hash",
        "totp_secret_enc",
        "totp_enabled",
        "is_active",
        "failed_login_count",
        "last_login_at",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert expected.issubset(cols)


def test_auth_user_indexes(_models_in_metadata) -> None:
    table = Base.metadata.tables["auth_user"]
    index_pairs = [set(idx.columns.keys()) for idx in table.indexes]
    # email_hash: index for HMAC-SHA256 lookup (C-03 §D1, ADR-007)
    assert {"tenant_id", "email_hash"} in index_pairs
    assert {"tenant_id", "deleted_at"} in index_pairs


def test_auth_session_table_exists(_models_in_metadata) -> None:
    assert "auth_session" in Base.metadata.tables


def test_auth_session_columns_and_jti_unique(_models_in_metadata) -> None:
    table = Base.metadata.tables["auth_session"]
    cols = {c.name for c in table.columns}
    for col in (
        "id",
        "tenant_id",
        "user_id",
        "refresh_token_hash",
        "jti",
        "issued_at",
        "expires_at",
        "last_used_at",
        "revoked_at",
        "ip_origen",
        "user_agent",
        "rotated_to_id",
        "replaced_by_id",
        "created_at",
        "updated_at",
        "deleted_at",
    ):
        assert col in cols
    jti_col = table.columns["jti"]
    assert jti_col.unique is True


def test_auth_session_user_id_fk_ondelete_cascade(_models_in_metadata) -> None:
    table = Base.metadata.tables["auth_session"]
    user_fk = next(fk for fk in table.foreign_keys if fk.column.table.name == "auth_user")
    assert user_fk.ondelete == "CASCADE"


def test_auth_session_self_fks_ondelete_set_null(_models_in_metadata) -> None:
    table = Base.metadata.tables["auth_session"]
    fk_targets = {(fk.column.table.name, fk.ondelete) for fk in table.foreign_keys}
    assert ("auth_session", "SET NULL") in fk_targets  # rotated_to_id, replaced_by_id
    # Two self-FKs (rotated_to_id, replaced_by_id)
    self_fks = [fk for fk in table.foreign_keys if fk.column.table.name == "auth_session"]
    assert len(self_fks) == 2


def test_auth_password_reset_table_and_selector_unique(_models_in_metadata) -> None:
    table = Base.metadata.tables["auth_password_reset"]
    assert table is not None
    selector = table.columns["selector"]
    assert selector.unique is True
    # A unique constraint on `selector` gives O(1) lookup; the project's
    # convention is `ux_<table>_<col>` for unique indexes.
    unique_idx_names = [i.name for i in table.indexes if i.unique]
    assert "ux_auth_password_reset_selector" in unique_idx_names


def test_auth_password_reset_user_id_fk_ondelete_cascade(_models_in_metadata) -> None:
    table = Base.metadata.tables["auth_password_reset"]
    user_fk = next(fk for fk in table.foreign_keys if fk.column.table.name == "auth_user")
    assert user_fk.ondelete == "CASCADE"
