"""Conftest for comunicacion tests."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_comunicacion_model_registered():
    """Ensure the Comunicacion model is registered with Base.metadata."""
    from app.modules.comunicacion.models.comunicacion import Comunicacion  # noqa: F401
    from app.models.tenant import Tenant  # noqa: F401
    from app.models.usuario import Usuario  # noqa: F401
    import app.auth.models  # noqa: F401
    import tests._fakes.models  # noqa: F401

    class _Dummy:
        pass

    return _Dummy()