"""Re-export of the declarative base for Alembic autogenerate.

This module exists to keep the model-package boundary clean: Alembic's
`env.py` imports `Base` from `app.models`, and models import `Base` from
`app.models` too. Putting the import through a dedicated `base` submodule
would only add an indirection — so we re-export from the package root
instead. The actual `Base` is still defined in `app.core.database` to
preserve the C-01 location of the SQLAlchemy declarative base.
"""

from app.core.database import Base

__all__ = ["Base"]
