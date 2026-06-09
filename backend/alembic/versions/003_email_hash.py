"""003: add auth_user.email_hash for deterministic email lookup (C-03 §D0 fix).

Run order:
    alembic upgrade head    # adds email_hash column + index
    alembic downgrade -1    # drops both (reversible)

Rationale: AES-256-GCM with a random nonce (C-02 `crypto.py`) is correct for
confidentiality but not for equality lookup. The `auth_user.email_hash`
column is a deterministic HMAC-SHA256 of `(tenant_id, email_lower)` keyed
by `ENCRYPTION_KEY`, indexed on `(tenant_id, email_hash)`. The
`AuthUserRepository.find_by_email` repo method searches on this column.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "003_email_hash"
down_revision: Union[str, None] = "002_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auth_user",
        sa.Column("email_hash", sa.String(length=64), nullable=False, server_default=""),
    )
    op.drop_index("ix_auth_user_tenant_email", table_name="auth_user")
    op.create_index(
        "ix_auth_user_tenant_email_hash",
        "auth_user",
        ["tenant_id", "email_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_user_tenant_email_hash", table_name="auth_user")
    op.create_index(
        "ix_auth_user_tenant_email",
        "auth_user",
        ["tenant_id", "email_enc"],
        unique=False,
    )
    op.drop_column("auth_user", "email_hash")
