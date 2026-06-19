"""`comunicacion` table — message dispatch with state machine.

States: Pendiente → Enviando → Enviado | Error | Cancelado
Enviado is terminal. Cancelado is terminal.
"""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security.crypto import CryptoError, decrypt, encrypt
from app.core.security.hashing import hash_email_for_search
from app.models.mixins import TenantScopedMixin


class ComunicacionEstado(str, enum.Enum):
    """Estado de una comunicación."""

    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"


class InvalidStateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted."""


TERMINAL_STATES = {ComunicacionEstado.ENVIADO, ComunicacionEstado.CANCELADO}
STATE_TRANSITIONS = {
    ComunicacionEstado.PENDIENTE: {ComunicacionEstado.ENVIANDO, ComunicacionEstado.CANCELADO},
    ComunicacionEstado.ENVIANDO: {ComunicacionEstado.ENVIADO, ComunicacionEstado.ERROR, ComunicacionEstado.CANCELADO},
    ComunicacionEstado.ENVIADO: set(),
    ComunicacionEstado.ERROR: {ComunicacionEstado.PENDIENTE},
    ComunicacionEstado.CANCELADO: set(),
}


def validate_transition(current: ComunicacionEstado, next_state: ComunicacionEstado) -> None:
    if current in TERMINAL_STATES and current != next_state:
        raise InvalidStateTransitionError(f"{current.value} is a terminal state.")
    if next_state not in STATE_TRANSITIONS.get(current, set()):
        allowed = ", ".join(s.value for s in STATE_TRANSITIONS.get(current, set())) or "none"
        raise InvalidStateTransitionError(
            f"Cannot transition from {current.value} to {next_state.value}. "
            f"Allowed transitions: {allowed}."
        )


class Comunicacion(Base, TenantScopedMixin):
    __tablename__ = "comunicacion"

    asunto: Mapped[str] = mapped_column(String(500), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    # Plaintext column retained for backward-compat fallback during migration only.
    # After migration 025 (backfill + drop), this column will be removed.
    destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    destinatario_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    destinatario_enc: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    estado: Mapped[ComunicacionEstado] = mapped_column(
        SAEnum(
            ComunicacionEstado,
            name="comunicacion_estado",
            values_callable=lambda x: [m.value for m in x],
        ),
        nullable=False,
        default=ComunicacionEstado.PENDIENTE,
    )
    lote_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    enviado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)

    __table_args__ = (
        Index("ix_comunicacion_estado", "estado"),
        Index("ix_comunicacion_lote_id", "lote_id"),
        Index("ix_comunicacion_tenant_estado", "tenant_id", "estado"),
        Index("ix_comunicacion_tenant_deleted", "tenant_id", "deleted_at"),
    )

    def transition_to(self, next_state: ComunicacionEstado) -> None:
        validate_transition(self.estado, next_state)
        self.estado = next_state
        if next_state == ComunicacionEstado.ENVIADO:
            self.enviado_at = datetime.now()

    def set_destinatario(self, plain: str) -> None:
        """Encrypt and hash the destinatario email.

        Stores only the encrypted value and hash lookup key.
        Does NOT store the plaintext email anywhere.
        """
        plain_lower = plain.strip().lower()
        self.destinatario_hash = hash_email_for_search(plain_lower, self.tenant_id)
        self.destinatario_enc = encrypt(plain_lower, tenant_id=self.tenant_id, aad_suffix="comunicacion.destinatario")

    def get_destinatario(self) -> str:
        """Decrypt the destinatario email.

        Returns the plaintext email by decrypting destinatario_enc.
        """
        if self.destinatario_enc:
            try:
                return decrypt(self.destinatario_enc, tenant_id=self.tenant_id, aad_suffix="comunicacion.destinatario")
            except (CryptoError, Exception):
                pass
        # Fallback to plaintext column (backward compat during migration)
        return self.destinatario