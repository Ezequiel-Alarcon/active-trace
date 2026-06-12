"""Padron file parser tests (T-7.5)."""

import io

import pytest

from app.services.padron_parser import (
    PadronParseError,
    parse_csv,
    parse_padron_file,
    parse_xlsx,
)


class TestParseXlsx:
    def test_parse_xlsx_returns_rows(self):
        wb_content = _make_xlsx_bytes([
            ["Nombre", "Apellidos", "Email", "Comision", "Regional"],
            ["Juan", "Pérez", "juan@example.com", "A", "CABA"],
            ["María", "García", "maria@example.com", "B", "GBA"],
        ])
        rows = parse_xlsx(wb_content)
        assert len(rows) == 2
        assert rows[0]["nombre"] == "Juan"
        assert rows[0]["apellidos"] == "Pérez"
        assert rows[0]["email"] == "juan@example.com"
        assert rows[0]["comision"] == "A"
        assert rows[0]["regional"] == "CABA"

    def test_parse_xlsx_normalizes_headers(self):
        wb_content = _make_xlsx_bytes([
            ["firstname", "last_name", "e-mail", "section", "sede"],
            ["Ana", "López", "ana@example.com", "C", "Rosario"],
        ])
        rows = parse_xlsx(wb_content)
        assert rows[0]["nombre"] == "Ana"
        assert rows[0]["apellidos"] == "López"
        assert rows[0]["email"] == "ana@example.com"
        assert rows[0]["comision"] == "C"
        assert rows[0]["regional"] == "Rosario"

    def test_parse_xlsx_skips_empty_rows(self):
        wb_content = _make_xlsx_bytes([
            ["Nombre", "Apellidos", "Email"],
            ["Juan", "Pérez", "juan@example.com"],
            [],  # empty
            ["María", "García", "maria@example.com"],
        ])
        rows = parse_xlsx(wb_content)
        assert len(rows) == 2

    def test_parse_xlsx_raises_on_missing_required_headers(self):
        wb_content = _make_xlsx_bytes([
            ["Nombre", "Apellidos"],  # missing Email
            ["Juan", "Pérez"],
        ])
        with pytest.raises(PadronParseError) as exc_info:
            parse_xlsx(wb_content)
        assert "email" in str(exc_info.value).lower()

    def test_parse_xlsx_raises_on_empty_file(self):
        wb_content = _make_xlsx_bytes([[]])
        with pytest.raises(PadronParseError) as exc_info:
            parse_xlsx(wb_content)
        assert "vacío" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()


class TestParseCsv:
    def test_parse_csv_returns_rows(self):
        content = "Nombre,Apellidos,Email,Comision\nJuan,Pérez,juan@example.com,A".encode("utf-8")
        rows = parse_csv(content)
        assert len(rows) == 1
        assert rows[0]["nombre"] == "Juan"
        assert rows[0]["apellidos"] == "Pérez"

    def test_parse_csv_falls_back_to_latin1(self):
        content = "Nombre,Apellidos,Email\nJuan,Pérez,juan@example.com".encode("latin-1")
        rows = parse_csv(content)
        assert rows[0]["apellidos"] == "Pérez"

    def test_parse_csv_raises_on_missing_required_headers(self):
        content = b"Nombre,Apellidos\nJuan,Perez"
        with pytest.raises(PadronParseError) as exc_info:
            parse_csv(content)
        assert "email" in str(exc_info.value).lower()


class TestParsePadronFile:
    def test_parse_padron_file_routes_xlsx(self):
        wb_content = _make_xlsx_bytes([
            ["Nombre", "Apellidos", "Email"],
            ["Juan", "Pérez", "juan@example.com"],
        ])
        rows = parse_padron_file(wb_content, "padron.xlsx")
        assert len(rows) == 1

    def test_parse_padron_file_routes_csv(self):
        content = b"Nombre,Apellidos,Email\nJuan,Perez,juan@example.com"
        rows = parse_padron_file(content, "padron.csv")
        assert len(rows) == 1

    def test_parse_padron_file_rejects_unsupported_format(self):
        content = b"some data"
        with pytest.raises(PadronParseError) as exc_info:
            parse_padron_file(content, "padron.pdf")
        assert "no soportado" in str(exc_info.value).lower()


def _make_xlsx_bytes(rows: list[list[str]]) -> bytes:
    """Build a minimal xlsx file from a list of rows using openpyxl."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()