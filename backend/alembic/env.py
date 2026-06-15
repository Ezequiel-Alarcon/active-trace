from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# TODO: (REVIEW) Las migraciones no siguen la numeración de CHANGES.md.
# C-04 dice "Migración 002" pero el archivo es 004_rbac_tables.py.
# La convención "una migración por change" quedó desactualizada frente
# a las migraciones acumulativas. Revisar y alinear.
from app.core.config import get_settings
from app.models import Base  # registers all ORM models on Base.metadata
from app.auth import models as _auth_models  # noqa: F401  (C-03 auth tables)
from app.rbac import models as _rbac_models  # noqa: F401  (C-04 RBAC tables)

config = context.config
settings = get_settings()
# Push the URL into Alembic's config so async_engine_from_config can read it.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()