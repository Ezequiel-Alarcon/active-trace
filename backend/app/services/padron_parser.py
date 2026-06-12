"""Padron file parser (C-09).

Parses .xlsx and .csv files exported from Moodle into padron rows.
Handles encoding detection (UTF-8 → Latin-1) and flexible header mapping.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import openpyxl


class PadronParseError(Exception):
    pass


_HEADER_ALIASES: dict[str, str] = {
    "nombre": "nombre",
    "firstname": "nombre",
    "first_name": "nombre",
    "nombre(s)": "nombre",
    "apellidos": "apellidos",
    "lastname": "apellidos",
    "last_name": "apellidos",
    "apellido": "apellidos",
    "email": "email",
    "correo": "email",
    "correo electrónico": "email",
    "e-mail": "email",
    "comision": "comision",
    "comisión": "comision",
    "section": "comision",
    "grupo": "comision",
    "regional": "regional",
    "sede": "regional",
    "campus": "regional",
}


def _normalize_header(header: str) -> str:
    return _HEADER_ALIASES.get(header.strip().lower(), header.strip().lower())


def _detect_column_mapping(headers: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for i, h in enumerate(headers):
        normalized = _normalize_header(h)
        if normalized in _HEADER_ALIASES.values() and normalized not in mapping:
            mapping[normalized] = i
    return mapping


def _map_row(row: list[str], mapping: dict[str, int]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field, idx in mapping.items():
        if idx < len(row):
            value = row[idx].strip() if row[idx] else None
            if value == "":
                value = None
            result[field] = value
        else:
            result[field] = None
    return result


def _decode_content(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def parse_xlsx(content: bytes) -> list[dict[str, Any]]:
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as e:
        raise PadronParseError(f"Archivo xlsx inválido: {e}") from e

    sheet = wb.active
    rows_iter = iter(sheet.iter_rows(values_only=True))

    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise PadronParseError("El archivo xlsx está vacío")

    if not header_row:
        raise PadronParseError("El archivo xlsx no tiene encabezados")

    headers = [str(h) if h is not None else "" for h in header_row]
    mapping = _detect_column_mapping(headers)

    required = {"nombre", "apellidos", "email"}
    missing = required - set(mapping.keys())
    if missing:
        raise PadronParseError(
            f"Encabezados requeridos faltantes: {', '.join(sorted(missing))}. "
            f"Encontrados: {', '.join(headers)}"
        )

    results: list[dict[str, Any]] = []
    for row in rows_iter:
        if not any(cell is not None for cell in row):
            continue
        row_data = _map_row(list(row), mapping)
        if row_data.get("nombre") or row_data.get("email"):
            results.append(row_data)

    wb.close()
    return results


def parse_csv(content: bytes) -> list[dict[str, Any]]:
    text = _decode_content(content)

    try:
        reader = csv.reader(io.StringIO(text))
        rows_iter = iter(reader)
    except Exception as e:
        raise PadronParseError(f"Archivo csv inválido: {e}") from e

    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise PadronParseError("El archivo csv está vacío")

    if not header_row:
        raise PadronParseError("El archivo csv no tiene encabezados")

    headers = [h.strip() for h in header_row]
    mapping = _detect_column_mapping(headers)

    required = {"nombre", "apellidos", "email"}
    missing = required - set(mapping.keys())
    if missing:
        raise PadronParseError(
            f"Encabezados requeridos faltantes: {', '.join(sorted(missing))}. "
            f"Encontrados: {', '.join(headers)}"
        )

    results: list[dict[str, Any]] = []
    for row in rows_iter:
        if not any(cell.strip() if cell else False for cell in row):
            continue
        row_data = _map_row(row, mapping)
        if row_data.get("nombre") or row_data.get("email"):
            results.append(row_data)

    return results


def parse_padron_file(content: bytes, filename: str) -> list[dict[str, Any]]:
    ext = filename.lower().split(".")[-1]
    if ext == "xlsx" or ext == "xls":
        return parse_xlsx(content)
    elif ext == "csv":
        return parse_csv(content)
    else:
        raise PadronParseError(
            f"Formato no soportado: .{ext}. Use .xlsx, .xls o .csv"
        )