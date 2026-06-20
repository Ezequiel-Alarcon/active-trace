FROM python:3.13-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY backend/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

FROM python:3.13-slim AS runtime
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY backend/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# App code
COPY backend/app ./app
# Alembic migrations
COPY backend/alembic ./alembic
# Seed scripts
COPY backend/scripts ./scripts

# alembic.ini for Docker: paths relative to /app (no backend/ prefix)
RUN printf '[alembic]\nscript_location = alembic\nprepend_sys_path = .\nversion_path_separator = os\n\n[loggers]\nkeys = root,sqlalchemy,alembic\n\n[handlers]\nkeys = console\n\n[formatters]\nkeys = generic\n\n[logger_root]\nlevel = WARN\nhandlers = console\nqualname =\n\n[logger_sqlalchemy]\nlevel = WARN\nhandlers =\nqualname = sqlalchemy.engine\n\n[logger_alembic]\nlevel = INFO\nhandlers =\nqualname = alembic\n\n[handler_console]\nclass = StreamHandler\nargs = (sys.stderr,)\nlevel = NOTSET\nformatter = generic\n\n[formatter_generic]\nformat = %%(levelname)-5.5s [%%(name)s] %%(message)s\ndatefmt = %%H:%%M:%%S\n' > /app/alembic.ini

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
