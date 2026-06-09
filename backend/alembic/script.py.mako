${message}

Revision: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


# ----------------------------------------------------------------------------
# REMINDER — activia-trace Alembic conventions (C-02, see ADR-002 + design D6)
#
# 1. Naming convention is enforced for ALL objects you create:
#      pk_<table>           primary key
#      fk_<table>_<target>  foreign key
#      uq_<table>_<cols>    unique constraint
#      ck_<table>_<col>     check constraint
#      ix_<table>_<col>     non-unique index
#      ux_<table>_<col>     unique index
#
# 2. If you are creating a DOMAIN table (anything other than the `tenant`
#    root or a global catalog), the table MUST inherit `TenantScopedMixin`
#    and therefore MUST include:
#      - `id`         UUID PK
#      - `tenant_id`  UUID NOT NULL, FK to `tenant.id` ON DELETE RESTRICT
#      - `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
#      - `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now() ON UPDATE now()
#      - `deleted_at` TIMESTAMPTZ NULL  (soft delete)
#    plus indexes: `ix_<table>_tenant`, `ix_<table>_tenant_deleted`.
#
# 3. Reverse the migration: every `upgrade()` MUST have a real `downgrade()`
#    that drops the objects it created.
# ----------------------------------------------------------------------------


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}