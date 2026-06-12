"""Tests para derivar_aprobado (C-10)."""

from app.domain.calificaciones.services.aprobado import derivar_aprobado


class TestDerivarAprobado:
    def test_null_nota_returns_false(self):
        assert derivar_aprobado(None, 60, ["A", "B", "C"]) is False

    def test_numeric_above_threshold_returns_true(self):
        assert derivar_aprobado(7.5, 60, None) is True

    def test_numeric_below_threshold_returns_false(self):
        assert derivar_aprobado(5.0, 60, None) is False

    def test_numeric_equal_to_threshold_returns_true(self):
        assert derivar_aprobado(60, 60, None) is True

    def test_string_in_conjunto_returns_true(self):
        assert derivar_aprobado("A", 60, ["A", "B+", "C", "7", "8", "9", "10"]) is True

    def test_string_not_in_conjunto_returns_false(self):
        assert derivar_aprobado("D", 60, ["A", "B+", "C", "7", "8", "9", "10"]) is False

    def test_list_with_any_match_returns_true(self):
        assert derivar_aprobado(["A", "D"], 60, ["A", "B+", "C"]) is True

    def test_list_with_no_match_returns_false(self):
        assert derivar_aprobado(["X", "Y"], 60, ["A", "B+", "C"]) is False

    def test_empty_conjunto_returns_false_for_string(self):
        assert derivar_aprobado("A", 60, None) is False

    def test_empty_conjunto_returns_false_for_list(self):
        assert derivar_aprobado(["A", "B"], 60, None) is False

    def test_float_threshold_comparison(self):
        assert derivar_aprobado(6.5, 70, None) is False
        assert derivar_aprobado(7.0, 70, None) is True

    def test_negative_numeric_returns_false(self):
        assert derivar_aprobado(-5, 60, None) is False

    def test_zero_threshold_all_positive_pass(self):
        assert derivar_aprobado(0.1, 0, None) is True

    def test_string_with_empty_conjunto(self):
        assert derivar_aprobado("Aprobado", 60, []) is False