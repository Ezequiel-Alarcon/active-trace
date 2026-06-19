"""Tests for (Real) column header detection (C-31 Bug 2 fix).

RN-01 specifies that columns ending in "(Real)" are numeric scores,
regardless of the prefix text.
"""

from app.domain.calificaciones.services.import_service import (
    _normalize_header,
    _detect_column_mapping,
    _REAL_SUFFIX_RE,
)


class TestRealSuffixRegex:
    """Tests for _REAL_SUFFIX_RE (C-31 Bug 2)."""

    def test_matches_lower_real(self):
        assert _REAL_SUFFIX_RE.search("nota (real)") is not None

    def test_matches_upper_real(self):
        assert _REAL_SUFFIX_RE.search("nota (Real)") is not None

    def test_matches_mixed_case_real(self):
        assert _REAL_SUFFIX_RE.search("nota (REAL)") is not None

    def test_matches_with_prefix(self):
        assert _REAL_SUFFIX_RE.search("Mi Nota (Real)") is not None

    def test_matches_calificacion_final_real(self):
        assert _REAL_SUFFIX_RE.search("Calificación Final (Real)") is not None

    def test_matches_grade_real(self):
        assert _REAL_SUFFIX_RE.search("Grade (real)") is not None

    def test_no_match_plain_nota(self):
        assert _REAL_SUFFIX_RE.search("nota") is None

    def test_no_match_parenthesis_not_at_end(self):
        assert _REAL_SUFFIX_RE.search("nota real") is None
        assert _REAL_SUFFIX_RE.search("(Real) nota") is None

    def test_no_match_real_without_parens(self):
        assert _REAL_SUFFIX_RE.search("nota real") is None


class TestNormalizeHeaderRealSuffix:
    """Tests for _normalize_header with (Real) suffix (C-31 Bug 2)."""

    def test_nota_real_normalizes_to_nota(self):
        assert _normalize_header("nota (real)") == "nota"

    def test_mi_nota_real_normalizes_to_nota(self):
        assert _normalize_header("Mi Nota (Real)") == "nota"

    def test_calificacion_final_real_normalizes_to_nota(self):
        assert _normalize_header("Calificación Final (Real)") == "nota"

    def test_grade_real_normalizes_to_nota(self):
        assert _normalize_header("Grade (real)") == "nota"

    def test_plain_nota_still_works(self):
        assert _normalize_header("nota") == "nota"

    def test_plain_calificacion_still_works(self):
        assert _normalize_header("calificacion") == "nota"

    def test_plain_grade_still_works(self):
        assert _normalize_header("grade") == "nota"

    def test_usuario_email_still_works(self):
        assert _normalize_header("email") == "usuario_email"


class TestDetectColumnMappingRealSuffix:
    """Tests for _detect_column_mapping with (Real) suffix headers (C-31 Bug 2)."""

    def test_detects_mi_nota_real(self):
        headers = ["usuario_email", "materia_id", "Mi Nota (Real)"]
        mapping = _detect_column_mapping(headers)
        assert mapping["usuario_email"] == 0
        assert mapping["materia_id"] == 1
        assert mapping["nota"] == 2

    def test_detects_calificacion_final_real(self):
        headers = ["email", "Calificación Final (Real)"]
        mapping = _detect_column_mapping(headers)
        assert mapping["usuario_email"] == 0
        assert mapping["nota"] == 1

    def test_mixed_real_and_alias_headers(self):
        headers = ["email", "materia_id", "nota (real)", "calificacion (real)"]
        mapping = _detect_column_mapping(headers)
        # First occurrence wins for each target column
        assert mapping["usuario_email"] == 0
        assert mapping["nota"] == 2
