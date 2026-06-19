# C-31: Fix Calificacion Logic Bugs

## Why

Three bugs in the calificaciones logic produce incorrect `aprobado` derivations and failed column detection:

1. `derivar_aprobado()` assumes 0-10 grade scale (`nota * 10 >= umbral_pct`), causing false negatives when LMS exports in 0-100 scale.
2. `import_service.py` header aliases match exact strings; columns like `"Mi Nota (Real)"` are not detected as numeric despite RN-01 stating any column ending in `(Real)` is numeric.
3. The hardcoded default `conjunto_aprobado` is `["A","B+","C","7","8","9","10"]` but KB RN-02 specifies `"Satisfactorio"` and `"Supera lo esperado"` as the passing textual values.

These bugs cause incorrect academic status (aprobado/atrasado) for students, directly affecting detection of atrasados, rankings, and reports.

## What Changes

- **Bug 1 Fix**: `derivar_aprobado()` receives `escala_max` param (default 10); threshold comparison becomes `nota / escala_max * 100 >= umbral_pct`
- **Bug 2 Fix**: `_detect_column_mapping()` uses regex `re.compile(r'\(real\)$', re.I)` to match any header ending with `(Real)` regardless of prefix
- **Bug 3 Fix**: `_DEFAULT_CONJUNTO` in `umbral_materia.py` and all `analisis_service.py` fallbacks changed to `["Satisfactorio", "Supera lo esperado"]`
- **Spec deltas**: Update `calificacion-import` and `umbral-materia` spec scenarios that hardcode the old default conjunto

## Capabilities

### New Capabilities

- (none — bugfix only)

### Modified Capabilities

- `calificacion-import`: Update header-detection scenario to reflect generic `(Real)` suffix detection (not just exact-match aliases)
- `umbral-materia`: Update default conjunto scenarios from `["A","B+","C","7","8","9","10"]` to `["Satisfactorio", "Supera lo esperado"]`; add `escala_max` parameter to aprobado derivation scenarios

## Impact

- **Files changed**:
  - `backend/app/domain/calificaciones/services/aprobado.py` — add `escala_max=10` param, fix comparison formula (línea ~32-33)
  - `backend/app/domain/calificaciones/services/import_service.py` — regex `_REAL_SUFFIX_RE` + `_normalize_header()` fix (líneas ~83-92)
  - `backend/app/domain/calificaciones/repositories/umbral_materia.py` — fix default conjunto
  - `backend/app/domain/analisis/services/analisis_service.py` — fix 4 default conjunto fallbacks
- **No DB migration needed** — logic-only fix
- **No API breaking changes** — new optional param `escala_max` defaults to 10 (backward compatible)
