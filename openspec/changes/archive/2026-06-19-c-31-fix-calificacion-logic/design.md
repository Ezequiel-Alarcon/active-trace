## Context

Three bugs in the calificaciones logic produce incorrect `aprobado` derivations:

1. **`aprobado.py:33`**: `return nota * 10 >= umbral_pct` assumes a 0-10 scale. The formula `nota * 10` is not a percentage normalization — multiplying by 10 is coincidentally correct only for 0-10 grades. On a 0-100 scale the same logic would give `nota=70 → 700 >= 60`, which happens to pass, but the math is meaningless (700 is not a percentage). The correct formula is `nota / escala_max * 100 >= umbral_pct`, which always produces a percentage regardless of scale.

2. **`import_service.py` (~líneas 83-92)**: `_normalize_header()` solo hacía lookup en `_HEADER_ALIASES`. Headers como `"Mi Nota (Real)"` o `"Calificación Final (Real)"` no eran detectados. El fix agrega `_REAL_SUFFIX_RE` y modifica `_normalize_header()` para hacer regex match antes del alias lookup.

3. **Default `conjunto_aprobado`**: The hardcoded default in `umbral_materia.py` is `["A","B+","C","7","8","9","10"]` but KB RN-02 specifies `"Satisfactorio"` and `"Supera lo esperado"` as the passing textual values. This bug is also propagated to 4 fallback sites in `analisis_service.py` (in `get_ranking`, `get_alumnos_atrasados`, `get_reporte_materia`, `get_notas_finales`).

## Goals / Non-Goals

**Goals:**
- Fix the scale-comparison formula in `derivar_aprobado()` to be scale-agnostic via `escala_max` parameter
- Fix header detection to use regex suffix match for `(Real)` per RN-01
- Fix default `conjunto_aprobado` to match KB RN-02

**Non-Goals:**
- No DB migration — purely logic/service-layer fix
- No breaking API changes — `escala_max` parameter defaults to 10 for backward compatibility
- No new permissions or audit changes

## Decisions

### Decision 1: Add `escala_max` parameter to `derivar_aprobado()` with default 10

**Choice**: Add `escala_max: int = 10` parameter to `derivar_aprobado()` and change the comparison from `nota * 10 >= umbral_pct` to `nota / escala_max * 100 >= umbral_pct`.

**Alternatives considered**:
- **Option A (rejected)**: Detect scale from data (e.g., check if any `nota > 10`). Risky — a valid 0-10 grade of `95` (rare but possible) would be misinterpreted.
- **Option B (rejected)**: Add `escala_max` column to `UmbralMateria` model. Requires DB migration and API changes for a bugfix of this severity.
- **Option C (chosen)**: Pass `escala_max` as a runtime parameter with a safe default of 10. No migration, backward-compatible, and the caller (import service or analisis service) can detect or infer the correct scale.

**Rationale**: The formula `nota / escala_max * 100 >= umbral_pct` correctly handles both 0-10 and 0-100 scales and any future scale.

### Decision 2: Regex-based `(Real)` suffix detection in `_detect_column_mapping()`

**Choice**: Before checking exact aliases, test each header against `re.compile(r'\(real\)$', re.I)`. If it matches, treat it as `nota`.

**Alternatives considered**:
- **Option A (rejected)**: Expand `_HEADER_ALIASES` with more exact strings. Not scalable — every LMS installation could use different prefixes.
- **Option B (chosen)**: Regex suffix match. Simple, per RN-01 spec, handles any prefix.

**Implementation note**: The regex check must happen BEFORE the exact-alias loop, to avoid false positives from the alias map.

### Decision 3: Change `_DEFAULT_CONJUNTO` to `["Satisfactorio", "Supera lo esperado"]`

**Choice**: Replace the hardcoded `["A","B+","C","7","8","9","10"]` with `["Satisfactorio", "Supera lo esperado"]` in `umbral_materia.py` and all four `analisis_service.py` fallback sites.

**Rationale**: KB RN-02 is explicit: passing textual values are `"Satisfactorio"` and `"Supera lo esperado"`. The old default was an artifact from a previous design iteration that never matched the KB.

## Risks / Trade-offs

- **[Risk] Existing imported data may have textual grades using the old scale** (e.g., `"A"`, `"B+"`). Changing the default conjunto means those grades would now be marked `aprobado=False` by default if no `UmbralMateria` is configured.
  - **Mitigation**: Any tenant that previously imported textual grades should already have an explicit `UmbralMateria` configured. The change only affects the fallback default for empty/missing configuration, which is the correct behavior per RN-02.

- **[Risk] `escala_max=10` default could cause issues if LMS exports 0-100 scale by default**
  - **Mitigation**: The caller can detect the scale from the data (e.g., if any `nota > 10`, assume 0-100) and pass the correct `escala_max`. The default of 10 preserves backward compatibility for existing 0-10 exports.

## Migration Plan

1. Deploy code changes (no DB migration needed)
2. Existing `UmbralMateria` records with explicit `conjunto_aprobado` are unaffected
3. Tenants without explicit `UmbralMateria` will now use the correct default `["Satisfactorio", "Supera lo esperado"]`
4. Rollback: revert code change — no data migration reversal needed

## Open Questions

- **Q1**: Should `escala_max` be inferred automatically from the imported data rather than requiring callers to detect and pass it?
  - **A**: Chosen approach keeps it explicit for now. If scale detection becomes a repeated pattern, it can be extracted to a utility function in a follow-up.
