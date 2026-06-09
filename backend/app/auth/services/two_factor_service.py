"""TOTP 2FA service (C-03 §4, D5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import pyotp

from app.auth.schemas import TwoFactorEnrollResponse, TwoFactorVerifyResponse
from app.core.config import get_settings
from app.core.security.crypto import decrypt, encrypt

logger = logging.getLogger("activia_trace.auth.two_factor")


class _SecretCarrier(Protocol):
    id: UUID
    tenant_id: UUID
    totp_secret_enc: str | None
    totp_enabled: bool


class _Session(Protocol):
    async def flush(self) -> None: ...


@dataclass
class TwoFactorService:
    issuer_label: str | None = None

    def __post_init__(self) -> None:
        if self.issuer_label is None:
            self.issuer_label = get_settings().TOTP_ISSUER

    def _encrypt(self, secret: str, tenant_id: UUID) -> str:
        return encrypt(secret, tenant_id=tenant_id, aad_suffix="auth_user.totp_secret")

    def _decrypt(self, blob: str, tenant_id: UUID) -> str:
        return decrypt(blob, tenant_id=tenant_id, aad_suffix="auth_user.totp_secret")

    def _label(self, user: _SecretCarrier) -> str:
        return f"{self.issuer_label}:{user.id}"

    def enroll(self, user: _SecretCarrier, session: _Session) -> TwoFactorEnrollResponse:
        secret = pyotp.random_base32(32)
        user.totp_secret_enc = self._encrypt(secret, user.tenant_id)
        user.totp_enabled = False
        # Caller flushes the session after returning
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=self._label(user), issuer_name=self.issuer_label)
        logger.info(
            "2fa enroll secret generated",
            extra={"action": "AUTH_2FA_ENROLL", "user_id": str(user.id)},
        )
        return TwoFactorEnrollResponse(otpauth_uri=uri, secret=secret)

    def verify(
        self, user: _SecretCarrier, session: _Session, code: str
    ) -> TwoFactorVerifyResponse:
        if not user.totp_secret_enc:
            return TwoFactorVerifyResponse(verified=False)
        try:
            secret = self._decrypt(user.totp_secret_enc, user.tenant_id)
        except Exception:
            logger.warning(
                "2fa verify failed: decrypt error",
                extra={"action": "AUTH_2FA_VERIFY_FAIL", "user_id": str(user.id)},
            )
            return TwoFactorVerifyResponse(verified=False)
        ok = pyotp.TOTP(secret).verify(code, valid_window=1)
        if ok:
            user.totp_enabled = True
            logger.info(
                "2fa verify ok",
                extra={"action": "AUTH_2FA_VERIFY_OK", "user_id": str(user.id)},
            )
        else:
            logger.warning(
                "2fa verify failed: invalid code",
                extra={"action": "AUTH_2FA_VERIFY_FAIL", "user_id": str(user.id)},
            )
        return TwoFactorVerifyResponse(verified=ok)
