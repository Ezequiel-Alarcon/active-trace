"""@audit decorator — automatic audit log entry on service method calls (C-05 §5)."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, ParamSpec, TypeVar

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repositories import AuditLogRepository

P = ParamSpec("P")
T = TypeVar("T")
logger = logging.getLogger(__name__)


def audit(
    action_code: str,
    *,
    get_detalle: Callable[..., dict[str, Any] | None] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that writes an AuditLog entry after the wrapped method succeeds.

    Usage:
        @audit("CALIFICACIONES_IMPORTAR")
        async def import_calificaciones(db: AsyncSession, ...) -> int:
            ...

    The decorator reads from `request.state` which must contain:
        - current_user.id        (UUID)
        - current_user.tenant_id (UUID)
        - impersonating          (bool)
        - impersonated_user_id    (UUID | None)

    IP and user agent are read from `request.state.ip` and
    `request.state.user_agent` if present, otherwise defaults.

    Fire-and-forget: audit write failures are logged but never propagate.
    """
    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(fn)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = await fn(*args, **kwargs)

            # Defer audit write to avoid blocking the response
            asyncio.create_task(
                _write_audit_log(
                    action_code=action_code,
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    get_detalle=get_detalle,
                )
            )
            return result

        @functools.wraps(fn)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = fn(*args, **kwargs)
            asyncio.create_task(
                _write_audit_log(
                    action_code=action_code,
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    get_detalle=get_detalle,
                )
            )
            return result

        # Preserve asyncio.iscoroutinefunction check
        import asyncio as _asyncio
        if _asyncio.iscoroutinefunction(fn):
            return async_wrapper  # type: ignore[return-type]
        return sync_wrapper  # type: ignore[return-type]

    return decorator


async def _write_audit_log(
    action_code: str,
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    result: Any,
    get_detalle: Callable[..., dict[str, Any] | None] | None,
) -> None:
    """Background task: extract context and write the audit entry.

    This runs after the main method completes. Failures are caught and logged.
    """
    try:
        # Extract request from args/kwargs
        request = _find_request(args, kwargs)
        if request is None:
            logger.warning(
                "audit: no Request found in %s; cannot write audit entry",
                fn.__name__,
            )
            return

        state = request.state

        # Actor and tenant
        current_user = getattr(state, "current_user", None)
        if current_user is None:
            logger.warning("audit: no current_user in request.state")
            return

        actor_id = getattr(current_user, "id", None)
        tenant_id = getattr(current_user, "tenant_id", None)
        if actor_id is None or tenant_id is None:
            logger.warning("audit: current_user missing id or tenant_id")
            return

        # Impersonation
        impersonating: bool = getattr(state, "impersonating", False)
        impersonated_user_id = getattr(state, "impersonated_user_id", None) if impersonating else None

        # Build detalle
        detalle = None
        if get_detalle is not None:
            detalle = get_detalle(*args, **kwargs)

        # filas_afectadas: use result if it's an int
        filas = int(result) if isinstance(result, int) else 0

        # IP and user agent
        ip = getattr(state, "ip", "0.0.0.0")
        user_agent = getattr(state, "user_agent", "unknown")

        # Write the entry (fire-and-forget)
        await _do_audit_write(
            tenant_id=tenant_id,
            actor_id=actor_id,
            accion=action_code,
            impersonado_id=impersonated_user_id,
            detalle=detalle,
            filas_afectadas=filas,
            ip=str(ip),
            user_agent=str(user_agent),
        )
    except Exception as exc:
        # Fire-and-forget: log and swallow
        logger.error("audit: failed to write AuditLog entry: %s", exc, exc_info=True)


def _find_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request | None:
    """Find a FastAPI Request in the decorated function's call arguments."""
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return kwargs.get("request")


async def _do_audit_write(
    tenant_id: Any,
    actor_id: Any,
    accion: str,
    impersonado_id: Any | None,
    detalle: dict[str, Any] | None,
    filas_afectadas: int,
    ip: str,
    user_agent: str,
) -> None:
    """Write the audit entry. Separated so it can be tested with a mock session."""
    try:
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            repo = AuditLogRepository(session, tenant_id)
            await repo.create(
                actor_id=actor_id,
                accion=accion,
                impersonado_id=impersonado_id,
                detalle=detalle,
                filas_afectadas=filas_afectadas,
                ip=ip,
                user_agent=user_agent,
            )
    except Exception as exc:
        logger.error("audit _do_audit_write failed: %s", exc, exc_info=True)