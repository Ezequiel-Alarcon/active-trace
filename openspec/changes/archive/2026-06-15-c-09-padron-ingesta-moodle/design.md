## Context

C-09 ya tiene una **base implementada y la migración `007_padron.py` aplicada**. Las piezas existentes son:

- `backend/app/models/padron.py` — `VersionPadron` (materia_id, cohorte_id, cargado_por, activa, `actividades=[]`) + `EntradaPadron` (version_id, `usuario_id` nullable, nombre, apellidos, **email en texto plano**, comision, regional). Ambos con `TenantScopedMixin` (tenant_id + soft delete).
- `backend/app/repositories/padron.py` — `PadronRepository`: `create_version_and_entries` (atómico), `get_active_version`, `deactivate_all`, `vaciar_datos` (soft-delete de versiones+entradas), `list_by_materia_cohorte`, `get_version_by_id`.
- `backend/app/services/padron.py` — `PadronService`: `preview` (parse sin persistir + matching de email→usuario_id), `import_padron` (crea versión activa y desactiva la previa), `vaciar_datos`, `activar_version`, validación de archivo (tamaño/extensión).
- `backend/app/services/padron_parser.py` — parser xlsx (openpyxl) y csv con `_decode_content` (UTF-8 → Latin-1) y mapeo flexible de encabezados.
- `backend/app/routers/padrones.py` — endpoints preview, import, list, entradas, activar, vaciar, moodle/sync (501 stub).
- `backend/app/integrations/moodle_ws.py` — `MoodleWSClient` con reintentos; `MoodleWSError(status_code=...)` ante 4xx/5xx/timeout.

El patrón canónico de PII cifrada vive en `Usuario` (C-07): pares `*_hash` (búsqueda determinística vía `hash_email_for_search(email_lower, tenant_id)`) + `*_enc` (AES-256-GCM vía `encrypt(plaintext, tenant_id=..., aad_suffix="<modelo>.<campo>")`), con `encrypt_usuario_fields` / `decrypt_usuario_fields` en el repositorio. La auditoría se emite con `audit_emit(<ACTION_CODE>, tenant_id=..., ...)` y el vocabulario de códigos es **cerrado** (`ACTION_CODES` en `app/core/audit.py`).

Constraints duros del proyecto: identidad siempre desde JWT; tenant_id en cada query; PII → AES-256; soft delete; RBAC `modulo:accion` fail-closed con `require_permission`; routers→services→repositories→models; tests sin mock de DB (DB efímera real); Strict TDD; ≤500 LOC/archivo; una migración Alembic por cambio de schema.

## Goals / Non-Goals

**Goals:**
- Cifrar `EntradaPadron.email` en reposo con AES-256, espejando el patrón de `Usuario`, e incluir la migración de datos de las filas existentes.
- Declarar el permiso RBAC `padron:vaciar` y aplicar las reglas de pertenencia RN-04/RN-05 en el vaciado.
- Corregir la auditoría de vaciado (hoy emite `PADRON_CARGAR`) introduciendo el código `PADRON_VACIAR`.
- Llevar el módulo a la cobertura exigida (≥80% líneas, ≥90% reglas de negocio) bajo Strict TDD, cubriendo versionado, import xlsx/csv, entrada sin usuario, autorización de vaciado, aislamiento multi-tenant y degradación de Moodle WS (502).

**Non-Goals:**
- Poblar `VersionPadron.actividades` (permanece `[]`; se completa en C-10).
- Sincronización nocturna automática contra Moodle WS (trabajo futuro). El endpoint `moodle/sync` mantiene su degradación controlada actual.
- Cambiar el contrato de `audit_emit`, del parser, o del `MoodleWSClient`.
- Re-crear cualquier archivo existente: este change **modifica y completa**, no reconstruye.

## Decisions

### D1 — Cifrado de email espejando `Usuario` (hash + enc), no cifrado inline ad-hoc
`EntradaPadron.email: String(2048)` se reemplaza por `email_hash: String(64)` (determinístico, para matching/joins) + `email_enc: String(2048)` (AES-256-GCM). Se añaden helpers `encrypt_entrada_fields(data, tenant_id)` / `decrypt_entrada_email(entrada)` en `repositories/padron.py`, con `aad_suffix="entrada_padron.email"`. El email se normaliza `strip().lower()` antes de hashear/cifrar, igual que `Usuario`.
**Por qué:** reusa el mecanismo auditado de C-07, mantiene el matching email→usuario_id (que hoy compara en lowercase) usando `email_hash` en vez de exponer texto plano, y satisface la regla dura "PII → AES-256".
**Alternativa descartada:** mantener un único campo cifrado sin hash → rompería el matching determinístico y el preview, obligando a descifrar todas las filas para comparar.

### D2 — Migración `021_padron_email_cifrado.py` cifra las filas existentes
Última migración: `020_mensajes_internos.py` → la siguiente es **`021`** (decisión registrada). La migración: (a) agrega columnas `email_hash`, `email_enc` (nullable temporal), (b) recorre las filas de `entrada_padron`, calcula hash+enc por `tenant_id` de la fila y los persiste, (c) borra la columna `email`, (d) marca `email_hash`/`email_enc` como `NOT NULL`. `downgrade` revierte recreando `email` plano (mejor esfuerzo, pierde el cifrado).
**Por qué:** una sola migración por cambio de schema; los datos existentes no pueden quedar en texto plano tras el deploy.
**Riesgo asumido:** la migración de datos usa la misma `crypto`/`hashing` de la app; debe importar las funciones dentro de la migración para reproducir AAD y key_id por tenant.

### D3 — Permiso `padron:vaciar` propio + reglas de pertenencia RN-04/RN-05
Se declara `padron:vaciar` en el catálogo (nueva migración de permiso, siguiendo el formato de `009_padron_permissions.py`) y se asigna a PROFESOR, COORDINADOR y ADMIN. El endpoint de vaciado deja de usar `padron:importar` y pasa a exigir `padron:vaciar`. **Regla de pertenencia (resuelve RN-04 vs RN-05):**
- **PROFESOR** solo puede vaciar una versión si `version.cargado_por == current_user.id`.
- **COORDINADOR** (y ADMIN) pueden vaciar cualquier versión del tenant (alcance global).
La verificación de pertenencia vive en el **service** (lógica de negocio), no en el router; el router solo declara `require_permission("padron:vaciar")` y pasa `current_user`.
**Por qué:** *vaciar* es destructivo y de criticidad distinta a *importar*; un permiso propio permite fail-closed fino. La pertenencia codifica RN-04/RN-05 sin un flag de superusuario.
**Nota de implementación (bug detectado):** el router actual invoca `require_permission("padron:...")` como **statement dentro del cuerpo** de la función, pero `require_permission` es un **factory** que devuelve una dependency — invocarlo así **no aplica el guard** (no hace nada). La forma correcta es `dependencies=[Depends(require_permission(...))]` o un parámetro `Depends(...)`. Esto se corrige en todos los endpoints de padrón como parte de D3.

### D4 — Auditoría: nuevo código `PADRON_VACIAR`, corrección del sink de vaciado
Se agrega `PADRON_VACIAR` a `ACTION_CODES` en `app/core/audit.py`. `PadronService.vaciar_datos` deja de emitir `PADRON_CARGAR` y emite `PADRON_VACIAR` con `tenant_id`, conteo de versiones afectadas y `materia_id`/`cohorte_id` en `detalle` (nunca PII). `import_padron` sigue emitiendo `PADRON_CARGAR`. Append-only por contrato de `audit_emit`.
**Por qué:** el código actual audita un vaciado como si fuera una carga — distorsiona el rastro. El vocabulario cerrado obliga a registrar el código nuevo explícitamente.

### D5 — Tests con DB efímera real y Moodle mockeado
Sin mocks de DB (regla dura): se usa la base de test real/contenedor efímero. El único colaborador mockeado es `MoodleWSClient` (integración externa): se simula `MoodleWSError(status_code=502)` para verificar que `moodle/sync` degrada a 502 con sugerencia de importación manual. Cada test sigue red→verde→triangulación→refactor; mínimo happy path + un caso borde por comportamiento.

## Risks / Trade-offs

- **[Migración de datos en `021` puede fallar a mitad si hay filas sin `tenant_id` válido]** → la migración valida por fila y usa `aad_suffix` fijo; se prueba contra una copia con datos sembrados antes del deploy; `downgrade` documentado.
- **[El bug del guard RBAC implica que hoy los endpoints de padrón corren sin chequeo de permiso real]** → es un hallazgo de seguridad CRÍTICO; se corrige en D3 y se cubre con un test que verifique 403 fail-closed sin el permiso. Se marca con `# TODO: (FIX)` en el router hasta su corrección.
- **[Cambiar `email` → `email_hash`+`email_enc` rompe lectores externos del campo plano]** → BREAKING declarado; el router de `entradas` devuelve el email **descifrado** vía el repositorio, preservando el contrato de respuesta de la API.
- **[Cobertura ≥90% de reglas de negocio es estricta para autorización de vaciado]** → se triangulan los tres caminos (PROFESOR propio OK, PROFESOR ajeno 403, COORDINADOR cualquiera OK) + aislamiento multi-tenant.

## Migration Plan

1. Aplicar `021_padron_email_cifrado.py` (schema + cifrado de filas existentes). Verificar conteo de filas migradas == filas previas.
2. Aplicar la migración de permiso `padron:vaciar` (catálogo + asignación a roles).
3. Deploy de código (modelo, repo, service, router, audit).
4. **Rollback:** `alembic downgrade` revierte el permiso y, para el schema, recrea `email` plano (mejor esfuerzo; el cifrado no es recuperable a texto plano sin descifrar primero — el `downgrade` descifra antes de soltar las columnas `*_enc`).

## Open Questions

- Ninguna bloqueante para C-09. La semántica de `actividades` y la sync automática quedan deferidas a C-10 / trabajo futuro por decisión de alcance.
