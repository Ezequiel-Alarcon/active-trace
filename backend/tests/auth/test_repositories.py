"""Strict TDD for app.auth.repositories (C-03 §2, D2, D3).

Spec contract:
- `AuthUserRepository.find_by_email(tenant_id, email_lower)` returns the unique
  active user for that (tenant, email). The composite index covers it.
- `AuthSessionRepository` exposes:
  - `find_by_jti(jti)` for the refresh-rotation use case.
  - `find_active_by_refresh_hash(hash)` for refresh-presentation lookup.
  - `revoke_chain(session_id) -> int` walks the rotated_to_id / replaced_by_id
    chain and revokes every active session in it. Capped at 100 hops.
  - `revoke_active_for_user(user_id)` revokes every active session for a user.
- `AuthPasswordResetRepository.find_by_selector(selector)` for the O(1) lookup.
- All three extend `TenantScopedRepository`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthPasswordReset, AuthSession, AuthUser
from app.auth.repositories import (
    AuthPasswordResetRepository,
    AuthSessionRepository,
    AuthUserRepository,
)
from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


@pytest_asyncio.fixture
async def db_setup():
    """Bring up an isolated schema in the test database and yield a session factory."""
    import os
    from app.models import tenant  # noqa: F401  (register Tenant)

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def tenant_ctx(db_setup):
    async with db_setup() as session:
        t = Tenant(codigo="UBA", nombre="Universidad", estado=TenantEstado.ACTIVO)
        session.add(t)
        await session.commit()
        await session.refresh(t)
    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


async def _make_user(
    session, tenant_id: UUID | None = None, email: str = "alice"
) -> AuthUser:
    tid = tenant_id or uuid4()
    u = AuthUser(
        tenant_id=tid,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tid),
        password_hash=hash_password("Pa55word!demo"),
    )
    session.add(u)
    await session.flush()
    return u


# ---------- AuthUserRepository.find_by_email ----------

async def test_find_by_email_returns_user_for_matching_tenant(
    db_setup, tenant_ctx
) -> None:
    tid = tenant_ctx
    async with db_setup() as session:
        await _make_user(session, tid)
        await session.commit()
    async with db_setup() as session:
        repo = AuthUserRepository(session, AuthUser, tid)
        user = await repo.find_by_email(tid, "alice")
        assert user is not None
        assert user.email_enc == "enc:alice"


async def test_find_by_email_returns_none_for_other_tenant(
    db_setup, tenant_ctx
) -> None:
    tid = tenant_ctx
    other_tid = uuid4()
    async with db_setup() as session:
        await _make_user(session, tid)
        await session.commit()
    async with db_setup() as session:
        repo = AuthUserRepository(session, AuthUser, other_tid)
        assert await repo.find_by_email(other_tid, "alice") is None


async def test_find_by_email_skips_soft_deleted(db_setup, tenant_ctx) -> None:
    tid = tenant_ctx
    async with db_setup() as session:
        u = await _make_user(session, tid)
        u.deleted_at = datetime.now(timezone.utc)
        await session.commit()
    async with db_setup() as session:
        repo = AuthUserRepository(session, AuthUser, tid)
        assert await repo.find_by_email(tid, "alice") is None


# ---------- AuthSessionRepository: chain walk ----------

async def _make_session(
    session, *, user_id, tenant_id, rotated_to_id=None, replaced_by_id=None, revoked=False
) -> AuthSession:
    now = datetime.now(timezone.utc)
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="h",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
        revoked_at=now if revoked else None,
        rotated_to_id=rotated_to_id,
        replaced_by_id=replaced_by_id,
    )
    session.add(s)
    await session.flush()
    return s


async def test_revoke_chain_linear(db_setup, tenant_ctx) -> None:
    tid = tenant_ctx
    async with db_setup() as session:
        u = await _make_user(session, tid)
        s1 = await _make_session(session, user_id=u.id, tenant_id=tid)
        s2 = await _make_session(session, user_id=u.id, tenant_id=tid, replaced_by_id=s1.id)
        s1.rotated_to_id = s2.id
        s3 = await _make_session(session, user_id=u.id, tenant_id=tid, replaced_by_id=s2.id)
        s2.rotated_to_id = s3.id
        await session.commit()
    async with db_setup() as session:
        repo = AuthSessionRepository(session, AuthSession, tid)
        count = await repo.revoke_chain(s1.id)
        assert count == 3
    async with db_setup() as session:
        from sqlalchemy import select
        rows = (await session.execute(select(AuthSession))).scalars().all()
        assert all(r.revoked_at is not None for r in rows)


async def test_revoke_chain_branching(db_setup, tenant_ctx) -> None:
    """If two branches share a parent, the walk must hit both branches
    and the parent (re-used from both leaves)."""
    tid = tenant_ctx
    async with db_setup() as session:
        u = await _make_user(session, tid)
        parent = await _make_session(session, user_id=u.id, tenant_id=tid)
        b1 = await _make_session(
            session, user_id=u.id, tenant_id=tid, replaced_by_id=parent.id
        )
        b2 = await _make_session(
            session, user_id=u.id, tenant_id=tid, replaced_by_id=parent.id
        )
        parent.rotated_to_id = b1.id
        await session.commit()
    async with db_setup() as session:
        repo = AuthSessionRepository(session, AuthSession, tid)
        count = await repo.revoke_chain(parent.id)
        assert count == 3


async def test_revoke_chain_respects_100_hop_cap(db_setup, tenant_ctx) -> None:
    """A pathological chain longer than 100 hops is truncated at 100."""
    tid = tenant_ctx
    async with db_setup() as session:
        u = await _make_user(session, tid)
        prev = await _make_session(session, user_id=u.id, tenant_id=tid)
        for _ in range(120):
            cur = await _make_session(
                session, user_id=u.id, tenant_id=tid, replaced_by_id=prev.id
            )
            prev.rotated_to_id = cur.id
            prev = cur
        await session.commit()
    async with db_setup() as session:
        repo = AuthSessionRepository(session, AuthSession, tid)
        count = await repo.revoke_chain(prev.id)
        assert count == 100


async def test_revoke_active_for_user(db_setup, tenant_ctx) -> None:
    tid = tenant_ctx
    async with db_setup() as session:
        u = await _make_user(session, tid)
        await _make_session(session, user_id=u.id, tenant_id=tid)
        await _make_session(session, user_id=u.id, tenant_id=tid, revoked=True)
        await session.commit()
    async with db_setup() as session:
        repo = AuthSessionRepository(session, AuthSession, tid)
        count = await repo.revoke_active_for_user(u.id)
        assert count == 1


# ---------- AuthPasswordResetRepository.find_by_selector ----------

async def test_find_by_selector_returns_row(db_setup, tenant_ctx) -> None:
    tid = tenant_ctx
    async with db_setup() as session:
        u = await _make_user(session, tid)
        pr = AuthPasswordReset(
            tenant_id=tid,
            user_id=u.id,
            selector="ABCDEFGH",
            token_hash="h",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        session.add(pr)
        await session.commit()
    async with db_setup() as session:
        repo = AuthPasswordResetRepository(session, AuthPasswordReset, tid)
        row = await repo.find_by_selector("ABCDEFGH")
        assert row is not None


async def test_find_by_selector_returns_none_for_unknown(db_setup, tenant_ctx) -> None:
    async with db_setup() as session:
        repo = AuthPasswordResetRepository(session, AuthPasswordReset, tenant_ctx)
        assert await repo.find_by_selector("ZZZZZZZZ") is None
