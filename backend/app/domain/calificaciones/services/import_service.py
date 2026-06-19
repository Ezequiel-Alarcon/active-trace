"""Import service for calificaciones (C-10).

Maneja el flujo de 2 pasos: preview (sin persistir) y confirm (persistir).
El preview_token tiene TTL de 15 minutos y es de un solo uso.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import openpyxl

from app.domain.calificaciones.repositories.calificacion import CalificacionRepository
from app.domain.calificaciones.schemas.calificacion import (
    CalificacionPreviewResponse,
    CalificacionPreviewRow,
)


class ImportServiceError(Exception):
    pass


class PreviewExpiredError(ImportServiceError):
    pass


class PreviewNotFoundError(ImportServiceError):
    pass


class CalificacionParseError(ImportServiceError):
    pass


_PREVIEW_TTL_MINUTES = 15


class _PreviewStore:
    """In-memory store for preview tokens (15-min TTL, single-use)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[datetime, list[dict[str, Any]]]] = {}

    def store(self, rows: list[dict[str, Any]]) -> str:
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=_PREVIEW_TTL_MINUTES)
        self._store[token] = (expires_at, rows)
        return token

    def consume(self, token: str) -> list[dict[str, Any]]:
        entry = self._store.pop(token, None)
        if entry is None:
            raise PreviewNotFoundError("Preview no encontrado o ya utilizado")
        expires_at, rows = entry
        if datetime.now(timezone.utc) > expires_at:
            raise PreviewExpiredError("Preview expirado")
        return rows


_preview_store = _PreviewStore()


_HEADER_ALIASES: dict[str, str] = {
    "usuario_email": "usuario_email",
    "email": "usuario_email",
    "correo": "usuario_email",
    "materia_id": "materia_id",
    "asignacion_id": "asignacion_id",
    "nota": "nota",
    "calificacion": "nota",
    "grade": "nota",
    "nota (real)": "nota",
    "calificacion (real)": "nota",
}

# Regex: matches any header ending with "(Real)" case-insensitively (RN-01)
_REAL_SUFFIX_RE = re.compile(r"\(real\)$", re.I)


def _normalize_header(header: str) -> str:
    stripped = header.strip()
    # RN-01: columns ending in "(Real)" are numeric scores
    if _REAL_SUFFIX_RE.search(stripped):
        return "nota"
    return _HEADER_ALIASES.get(stripped.lower(), stripped.lower())


def _detect_column_mapping(headers: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for i, h in enumerate(headers):
        normalized = _normalize_header(h)
        if normalized in _HEADER_ALIASES.values() and normalized not in mapping:
            mapping[normalized] = i
    return mapping


def _decode_content(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _parse_nota(value: str | None) -> dict | list | float | int | str | None:
    if value is None or value == "":
        return None
    value = value.strip()
    if value.startswith("["):
        import json
        try:
            return json.loads(value)
        except Exception:
            return value
    if value.startswith("{"):
        import json
        try:
            return json.loads(value)
        except Exception:
            return value
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_calificaciones_xlsx(content: bytes) -> list[dict[str, Any]]:
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as e:
        raise CalificacionParseError(f"Archivo xlsx inválido: {e}") from e

    sheet = wb.active
    rows_iter = iter(sheet.iter_rows(values_only=True))

    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise CalificacionParseError("El archivo xlsx está vacío")

    if not header_row:
        raise CalificacionParseError("El archivo xlsx no tiene encabezados")

    headers = [str(h) if h is not None else "" for h in header_row]
    mapping = _detect_column_mapping(headers)

    required = {"usuario_email", "materia_id"}
    missing = required - set(mapping.keys())
    if missing:
        raise CalificacionParseError(
            f"Encabezados requeridos faltantes: {', '.join(sorted(missing))}. "
            f"Encontrados: {', '.join(headers)}"
        )

    results: list[dict[str, Any]] = []
    for row in rows_iter:
        if not any(cell is not None for cell in row):
            continue
        row_list = list(row)
        row_data: dict[str, Any] = {}
        for field, idx in mapping.items():
            if idx < len(row_list):
                row_data[field] = row_list[idx]
            else:
                row_data[field] = None
        results.append(row_data)

    wb.close()
    return results


def parse_calificaciones_csv(content: bytes) -> list[dict[str, Any]]:
    text = _decode_content(content)

    try:
        reader = csv.reader(io.StringIO(text))
        rows_iter = iter(reader)
    except Exception as e:
        raise CalificacionParseError(f"Archivo csv inválido: {e}") from e

    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise CalificacionParseError("El archivo csv está vacío")

    if not header_row:
        raise CalificacionParseError("El archivo csv está vacío")

    headers = [h.strip() for h in header_row]
    mapping = _detect_column_mapping(headers)

    required = {"usuario_email", "materia_id"}
    missing = required - set(mapping.keys())
    if missing:
        raise CalificacionParseError(
            f"Encabezados requeridos faltantes: {', '.join(sorted(missing))}. "
            f"Encontrados: {', '.join(headers)}"
        )

    results: list[dict[str, Any]] = []
    for row in rows_iter:
        if not any(cell.strip() if cell else False for cell in row):
            continue
        row_data: dict[str, Any] = {}
        for field, idx in mapping.items():
            if idx < len(row):
                row_data[field] = row[idx]
            else:
                row_data[field] = None
        results.append(row_data)

    return results


def parse_calificaciones_file(content: bytes, filename: str) -> list[dict[str, Any]]:
    ext = filename.lower().split(".")[-1]
    if ext in ("xlsx", "xls"):
        return parse_calificaciones_xlsx(content)
    elif ext == "csv":
        return parse_calificaciones_csv(content)
    else:
        raise CalificacionParseError(
            f"Formato no soportado: .{ext}. Use .xlsx, .xls o .csv"
        )


class ImportService:
    def __init__(
        self,
        session: Any,
        tenant_id: UUID,
        usuario_ids_by_email: dict[str, UUID],
        materia_ids: set[UUID],
        asignacion_ids: set[UUID],
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._usuario_ids_by_email = usuario_ids_by_email
        self._materia_ids = materia_ids
        self._asignacion_ids = asignacion_ids
        self._repo = CalificacionRepository(session, tenant_id)

    def parse_preview(
        self,
        file_content: bytes,
        filename: str,
        is_completion: bool = False,
    ) -> CalificacionPreviewResponse:
        try:
            raw_rows = parse_calificaciones_file(file_content, filename)
        except CalificacionParseError as e:
            raise ImportServiceError(str(e)) from e

        seen: set[tuple[str, str]] = set()
        preview_rows: list[CalificacionPreviewRow] = []
        processed_rows: list[dict[str, Any]] = []

        for raw in raw_rows:
            warnings: list[str] = []
            valid = True

            usuario_email = str(raw.get("usuario_email") or "").strip().lower()
            materia_id_str = str(raw.get("materia_id") or "").strip()
            asignacion_id_str = str(raw.get("asignacion_id") or "").strip() or None

            usuario_id = self._usuario_ids_by_email.get(usuario_email)
            if usuario_id is None:
                warnings.append(f"Usuario no encontrado: {usuario_email}")
                valid = False

            try:
                materia_id = UUID(materia_id_str) if materia_id_str else None
            except (ValueError, NameError):
                materia_id = None

            if materia_id is None or materia_id not in self._materia_ids:
                warnings.append(f"Materia no encontrada: {materia_id_str}")
                valid = False

            asignacion_id: UUID | None = None
            if asignacion_id_str:
                try:
                    asignacion_id = UUID(asignacion_id_str)
                except ValueError:
                    warnings.append(f"Asignacion ID inválido: {asignacion_id_str}")
                    valid = False
                else:
                    if asignacion_id not in self._asignacion_ids:
                        warnings.append(f"Asignacion no encontrada: {asignacion_id_str}")
                        valid = False

            nota: dict | list | float | int | str | None = None
            if not is_completion:
                nota_raw = raw.get("nota")
                if nota_raw is not None:
                    nota = _parse_nota(str(nota_raw))

            row_key = (str(usuario_id), str(asignacion_id) if asignacion_id else "")
            if row_key in seen:
                warnings.append("Duplicado en archivo para este usuario y asignación")
                valid = False
            seen.add(row_key)

            preview_rows.append(CalificacionPreviewRow(
                usuario_id=usuario_id,
                materia_id=materia_id,
                asignacion_id=asignacion_id,
                nota=nota,
                valid=valid,
                warnings=warnings,
            ))
            processed_rows.append({
                "usuario_id": usuario_id,
                "materia_id": materia_id,
                "asignacion_id": asignacion_id,
                "nota": nota,
            })

        preview_token = _preview_store.store(processed_rows)
        return CalificacionPreviewResponse(
            preview_token=preview_token,
            rows=preview_rows,
            total=len(preview_rows),
            filename=filename,
        )

    async def confirm_import(
        self,
        preview_token: str,
        created_by: UUID,
    ) -> tuple[int, int, int]:
        try:
            rows = _preview_store.consume(preview_token)
        except PreviewNotFoundError as e:
            raise ImportServiceError("Preview no encontrado o ya utilizado") from e
        except PreviewExpiredError as e:
            raise ImportServiceError("Preview expirado") from e

        import_batch_id = uuid.uuid4()
        persisted = 0
        skipped = 0
        failed = 0

        valid_rows = [r for r in rows if r.get("usuario_id") is not None]

        for row_data in valid_rows:
            try:
                exists = await self._repo.exists_for_materia_usuario_asignacion(
                    materia_id=row_data["materia_id"],
                    usuario_id=row_data["usuario_id"],
                    asignacion_id=row_data.get("asignacion_id"),
                )
                if exists:
                    skipped += 1
                    continue

                await self._repo.create_many(
                    rows_data=[row_data],
                    import_batch_id=import_batch_id,
                    created_by=created_by,
                )
                persisted += 1
            except Exception:
                failed += 1

        total = len(valid_rows)
        from app.core.audit import audit_emit
        from app.audit.constants import AUDIT_CALIFICACIONES_IMPORTAR
        await audit_emit(
            self._session,
            AUDIT_CALIFICACIONES_IMPORTAR,
            actor_id=created_by,
            tenant_id=self._tenant_id,
            detalle={
                "import_batch_id": str(import_batch_id),
                "total_filas": total,
                "persistidas": persisted,
                "omitidas": skipped,
            },
        )
        return persisted, skipped, failed