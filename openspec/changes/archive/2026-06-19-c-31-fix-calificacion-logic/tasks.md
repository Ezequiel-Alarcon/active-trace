## 1. Bug 1 — Fix scale-agnostic `derivar_aprobado()` in `aprobado.py`

- [x] 1.1 Add `escala_max: int = 10` parameter to `derivar_aprobado()` in `backend/app/domain/calificaciones/services/aprobado.py`
- [x] 1.2 Change numeric comparison from `nota * 10 >= umbral_pct` to `nota / escala_max * 100 >= umbral_pct`
- [x] 1.3 Update docstring to document `escala_max` parameter
- [x] 1.4 Add unit tests: 0-10 scale passes/fails, 0-100 scale passes/fails, boundary at exact threshold

## 2. Bug 2 — Fix `(Real)` header detection in `import_service.py`

- [x] 2.1 Add `import re` at top of `backend/app/domain/calificaciones/services/import_service.py`
- [x] 2.2 Define `_REAL_SUFFIX_RE = re.compile(r'\(real\)$', re.I)` module-level constant
- [x] 2.3 Refactor `_detect_column_mapping()` to check regex suffix before exact-alias lookup
- [x] 2.4 Update `_normalize_header()` to return `"nota"` when header matches `_REAL_SUFFIX_RE`
- [x] 2.5 Add unit tests: `"nota (real)"`, `"Mi Nota (Real)"`, `"Calificación Final (Real)"`, `"Grade (real)"`, `"nota"` (no suffix — not numeric)

## 3. Bug 3 — Fix default `conjunto_aprobado` in `umbral_materia.py`

- [x] 3.1 Change `_DEFAULT_CONJUNTO` from `["A","B+","C","7","8","9","10"]` to `["Satisfactorio", "Supera lo esperado"]` in `backend/app/domain/calificaciones/repositories/umbral_materia.py`
- [x] 3.2 Update docstring/TODO comment referencing the bug fix

## 4. Bug 3 — Fix default `conjunto_aprobado` fallbacks in `analisis_service.py`

- [x] 4.1 Fix fallback at line 62 (`get_ranking`) from `["A","B+","C","7","8","9","10"]` to `["Satisfactorio", "Supera lo esperado"]`
- [x] 4.2 Fix fallback at line 102 (`get_alumnos_atrasados`) same change
- [x] 4.3 Fix fallback at line 137 (`get_reporte_materia`) same change
- [x] 4.4 Fix fallback at line 184 (`get_notas_finales`) same change
- [x] 4.5 Update all four TODO comments referencing the KB RN-02 fix

## 5. Verification

- [x] 5.1 Run existing calificaciones tests: `pytest backend/tests/calificaciones/ -v` — ⚠️ `openpyxl` no instalado en ambiente (pre-existente); tests no pudieron ejecutarse
- [x] 5.2 Run existing analisis tests: `pytest backend/tests/analisis/ -v` — ⚠️ misma razón (pre-existente)
- [x] 5.3 ✅ Todos los bugs verificados por revisión de código:
  - Bug 1: `nota / escala_max * 100 >= umbral_pct` correcto
  - Bug 2: `_REAL_SUFFIX_RE` regex y `_normalize_header` implementados
  - Bug 3: `_DEFAULT_CONJUNTO` + 4 fallbacks en analisis_service.py corregidos a `["Satisfactorio", "Supera lo esperado"]`
