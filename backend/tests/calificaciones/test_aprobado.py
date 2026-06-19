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


# ── Tests for escala_max (C-31 Bug 1 fix) ──────────────────────────────────────

    def test_escala_max_10_passing(self):
        """On 0-10 scale: nota=7, umbral=60 → 7/10*100=70 >= 60 → True."""
        assert derivar_aprobado(7, 60, None, escala_max=10) is True

    def test_escala_max_10_failing(self):
        """On 0-10 scale: nota=5, umbral=60 → 5/10*100=50 < 60 → False."""
        assert derivar_aprobado(5, 60, None, escala_max=10) is False

    def test_escala_max_10_boundary(self):
        """On 0-10 scale: nota=6, umbral=60 → 6/10*100=60 >= 60 → True."""
        assert derivar_aprobado(6, 60, None, escala_max=10) is True

    def test_escala_max_100_passing(self):
        """On 0-100 scale: nota=70, umbral=60 → 70/100*100=70 >= 60 → True."""
        assert derivar_aprobado(70, 60, None, escala_max=100) is True

    def test_escala_max_100_failing(self):
        """On 0-100 scale: nota=50, umbral=60 → 50/100*100=50 < 60 → False."""
        assert derivar_aprobado(50, 60, None, escala_max=100) is False

    def test_escala_max_100_boundary(self):
        """On 0-100 scale: nota=60, umbral=60 → 60/100*100=60 >= 60 → True."""
        assert derivar_aprobado(60, 60, None, escala_max=100) is True


# ── Tests for RN-02 conjunto_aprobado default (C-31 Bug 3 fix) ─────────────────

    def test_rn02_default_conjunto_satisfactorio(self):
        """KB RN-02: 'Satisfactorio' is a passing textual value."""
        conjunto = ["Satisfactorio", "Supera lo esperado"]
        assert derivar_aprobado("Satisfactorio", 60, conjunto) is True

    def test_rn02_default_conjunto_supera(self):
        """KB RN-02: 'Supera lo esperado' is a passing textual value."""
        conjunto = ["Satisfactorio", "Supera lo esperado"]
        assert derivar_aprobado("Supera lo esperado", 60, conjunto) is True

    def test_rn02_default_conjunto_non_passing(self):
        """KB RN-02: values outside the conjunto are not passing."""
        conjunto = ["Satisfactorio", "Supera lo esperado"]
        assert derivar_aprobado("A", 60, conjunto) is False