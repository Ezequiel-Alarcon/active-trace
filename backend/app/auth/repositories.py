"""Auth repositories (C-03 §2, D2, D3).

All three extend `TenantScopedRepository[T]`. Public methods:
- `AuthUserRepository.find_by_email(tenant_id, email_lower)` — login lookup.
- `AuthSessionRepository.find_by_jti`, `find_active_by_refresh_hash`,
  `revoke_chain(session_id) -> int`, `revoke_active_for_user(user_id) -> int`.
- `AuthPasswordResetRepository.find_by_selector(selector)`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from collections import deque

from sqlalchemy import select, update

from app.auth.models import AuthPasswordReset, AuthSession, AuthUser
from app.core.security.hashing import hash_email_for_search
from app.repositories.base import TenantScopedRepository


_CHAIN_WALK_CAP: int = 100


class AuthUserRepository(TenantScopedRepository[AuthUser]):
    async def find_by_email(
        self, tenant_id: UUID, email_lower: str
    ) -> AuthUser | None:
        """Lookup the active user by (tenant, email) using a deterministic
        HMAC of `(tenant_id, email_lower)` keyed by `ENCRYPTION_KEY`.

        The HMAC is stored in `auth_user.email_hash` (indexed). The
        `email_enc` column carries the AES-GCM ciphertext (confidentiality)
        but is not used for lookup because the nonce is random.
        """
        email_hash = hash_email_for_search(email_lower, tenant_id)
        stmt = (
            select(AuthUser)
            .where(AuthUser.tenant_id == tenant_id)
            .where(AuthUser.email_hash == email_hash)
            .where(AuthUser.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class AuthSessionRepository(TenantScopedRepository[AuthSession]):
    async def find_all_active(self) -> list[AuthSession]:
        """Cross-tenant: returns all non-revoked sessions."""
        stmt = select(AuthSession).where(AuthSession.revoked_at.is_(None))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_all(self) -> list[AuthSession]:
        """Cross-tenant: returns all sessions (including revoked)."""
        stmt = select(AuthSession)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_jti(self, jti: UUID) -> AuthSession | None:
        stmt = select(AuthSession).where(AuthSession.jti == jti)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_refresh_hash(
        self, tenant_id: UUID, refresh_token_hash: str
    ) -> AuthSession | None:
        stmt = (
            select(AuthSession)
            .where(AuthSession.tenant_id == tenant_id)
            .where(AuthSession.refresh_token_hash == refresh_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .where(AuthSession.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_chain(self, session_id: UUID) -> int:
        """Walk the rotated_to_id / replaced_by_id chain and revoke every
        active session in it. Bounded by `_CHAIN_WALK_CAP` hops.

        The chain is a small graph: from a node `n`, the reachable set
        includes `n.rotated_to_id` (the primary successor), every session
        whose `replaced_by_id == n.id` (branch successors that rotated
        from `n`), and `n.replaced_by_id` (the predecessor — needed to
        walk a chain backwards from a leaf). We BFS over the union of
        these edges, bounded by `_CHAIN_WALK_CAP` visited nodes, then
        revoke the visited set in a single UPDATE and commit so the
        revocation is durable across subsequent sessions.
        """
        to_revoke: list[UUID] = []
        visited: set[UUID] = set()
        queue: deque[UUID] = deque([session_id])
        while queue and len(to_revoke) < _CHAIN_WALK_CAP:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            to_revoke.append(current)
            row_stmt = select(
                AuthSession.rotated_to_id,
                AuthSession.replaced_by_id,
            ).where(AuthSession.id == current)
            row = (await self._session.execute(row_stmt)).first()
            if row is not None:
                rot, rep = row[0], row[1]
                if rot is not None and rot not in visited:
                    queue.append(rot)
                if rep is not None and rep not in visited:
                    queue.append(rep)
            children_stmt = select(AuthSession.id).where(
                AuthSession.replaced_by_id == current
            )
            for child_id in (
                await self._session.execute(children_stmt)
            ).scalars().all():
                if child_id not in visited:
                    queue.append(child_id)
        if not to_revoke:
            return 0
        now = datetime.now(timezone.utc)
        update_stmt = (
            update(AuthSession)
            .where(AuthSession.id.in_(to_revoke))
            .where(AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = await self._session.execute(update_stmt)
        await self._session.commit()
        return int(result.rowcount or 0)

    async def revoke_active_for_user(self, user_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(AuthSession)
            .where(AuthSession.user_id == user_id)
            .where(AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return int(result.rowcount or 0)


class AuthPasswordResetRepository(TenantScopedRepository[AuthPasswordReset]):
    async def find_by_selector(self, selector: str) -> AuthPasswordReset | None:
        stmt = (
            select(AuthPasswordReset)
            .where(AuthPasswordReset.selector == selector)
            .where(AuthPasswordReset.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
