# Tasks — C-09 padron-ingesta-moodle

> Strict TDD en cada tarea de test: red (test que falla) → green (código mínimo) → triangulate (≥2 casos: happy + borde) → refactor.
> Reglas duras aplicadas: identidad desde JWT, tenant_id en cada query, PII→AES-256, soft delete, RBAC fail-closed, routers→services→repositories→models, sin mock de DB, ≤500 LOC/archivo, una migración por cambio de schema.

## 1. Cifrado AES-256 del email + migración 021

- [x] 1.1 RED: test de repositorio que falla — al crear entradas, `entrada_padron` persiste `email_hash` + `email_enc` y NO una columna `email` en texto plano (DB efímera real).
- [x] 1.2 GREEN: modificar `app/models/padron.py` — reemplazar `EntradaPadron.email` por `email_hash: String(64)` + `email_enc: String(2048)` (ambos NOT NULL).
- [x] 1.3 GREEN: agregar helpers `encrypt_entrada_fields(data, tenant_id)` / `decrypt_entrada_email(entrada)` en `app/repositories/padron.py` usando `encrypt`/`hash_email_for_search` con `aad_suffix="entrada_padron.email"` y email normalizado `strip().lower()`; cifrar en `create_version_and_entries`.
- [x] 1.4 TRIANGULATE: test de lectura — `get_entries_by_version` + descifrado devuelve el email en claro; test de matching email→usuario usando `email_hash` determinístico (caso match y caso sin match).
- [x] 1.5 GREEN: ajustar `services/padron.py` (preview/import) y `routers/padrones.py` (endpoint `entradas`) para descifrar el email en la respuesta, preservando el contrato de la API.
- [x] 1.6 GREEN: crear migración `backend/alembic/versions/021_padron_email_cifrado.py` (down_revision `020_mensajes_internos`): add `email_hash`/`email_enc` nullable → cifrar filas existentes por `tenant_id` → drop `email` → set NOT NULL. `downgrade`: descifrar a `email` plano y soltar columnas `*_enc`/`*_hash`.
- [x] 1.7 REFACTOR: eliminar duplicación, verificar ≤500 LOC, correr la suite de cifrado en verde.

## 2. Permiso RBAC `padron:vaciar`

- [x] 2.1 RED: test que falla — un usuario sin `padron:vaciar` recibe 403 al invocar el endpoint de vaciado (fail-closed).
- [x] 2.2 GREEN: corregir el bug del guard — usar `dependencies=[Depends(require_permission("padron:vaciar"))]` en el endpoint de vaciado (y revisar los demás endpoints de padrón que invocan el factory como statement sin efecto). Marcar el hallazgo con `# TODO: (FIX)` donde corresponda hasta corregirlo.
- [x] 2.3 GREEN: crear migración de permiso `padron:vaciar` siguiendo el formato de `009_padron_permissions.py` — alta en `permiso` + asignación a PROFESOR, COORDINADOR y ADMIN.
- [x] 2.4 TRIANGULATE: test con permiso presente → la autorización RBAC pasa (luego se combina con pertenencia en grupo 3); test que confirma que el vaciado ya NO acepta solo `padron:importar`.
- [x] 2.5 REFACTOR: limpiar y correr la suite RBAC en verde.

## 3. Tests de comportamiento (Strict TDD)

- [x] 3.1 RED→GREEN→TRIANGULATE: versionado — importar/activar una versión la deja `activa=true` y desactiva la previa de la misma `(materia, cohorte)` (caso import y caso activar explícito).
- [x] 3.2 RED→GREEN→TRIANGULATE: import xlsx — preview NO persiste; confirmación crea versión+entradas atómicamente (happy + archivo con extensión peligrosa rechazado 400).
- [x] 3.3 RED→GREEN→TRIANGULATE: import csv — fallback de encoding UTF-8 → Latin-1 (csv UTF-8 OK + csv Latin-1 con acentos OK).
- [x] 3.4 RED→GREEN→TRIANGULATE: entrada sin `usuario_id` — email sin usuario del tenant se persiste con `usuario_id = NULL` (caso sin match + caso con match poblando usuario_id).
- [x] 3.5 RED: vaciado — PROFESOR vaciando versión ajena (`cargado_por != current_user.id`) → 403 y ninguna fila modificada.
- [x] 3.6 GREEN: implementar la regla de pertenencia en `services/padron.py` (`vaciar_datos` recibe `current_user` con rol/id; PROFESOR solo `cargado_por == current_user.id`, COORDINADOR/ADMIN global). El router declara el permiso; la lógica vive en el service.
- [x] 3.7 TRIANGULATE: PROFESOR vacía su propia versión → OK (soft delete); COORDINADOR vacía versión ajena → OK.
- [x] 3.8 RED→GREEN→TRIANGULATE: aislamiento multi-tenant — un tenant no ve ni vacía versiones/entradas de otro tenant (lectura cruzada vacía + vaciado no afecta otro tenant).
- [x] 3.9 RED→GREEN→TRIANGULATE: Moodle WS — mock del `MoodleWSClient`: `MoodleWSError(status_code=502)` → endpoint responde 502 con sugerencia de import manual; caso Moodle WS no configurado → 502.

## 4. Auditoría PADRON_CARGAR / PADRON_VACIAR

- [x] 4.1 RED: test que falla — vaciar emite `PADRON_VACIAR` (y NO `PADRON_CARGAR`); el código existe en el vocabulario cerrado.
- [x] 4.2 GREEN: agregar `PADRON_VACIAR` a `ACTION_CODES` en `app/core/audit.py`.
- [x] 4.3 GREEN: corregir `PadronService.vaciar_datos` para emitir `PADRON_VACIAR` con `tenant_id` y conteo de versiones afectadas (sin PII en `detalle`).
- [x] 4.4 TRIANGULATE: test que confirma que `import_padron` sigue emitiendo `PADRON_CARGAR` con `filas_afectadas=N` y sin PII; verificar append-only.
- [x] 4.5 REFACTOR: limpiar, correr la suite completa de padrón en verde y verificar cobertura ≥80% líneas / ≥90% reglas de negocio.
