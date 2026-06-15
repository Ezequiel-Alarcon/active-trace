## Why

La ingesta de padrón de alumnos (C-09) ya tiene una base implementada (modelos, repositorio, servicio, parser xlsx/csv, router y migración aplicada), pero arrastra defectos de seguridad y cobertura que la hacen inaceptable para producción multi-tenant: el email del alumno —PII— se persiste en **texto plano**, la operación destructiva *vaciar padrón* no tiene un permiso RBAC propio ni respeta las reglas de pertenencia RN-04/RN-05, la auditoría de carga/vaciado es incorrecta, y prácticamente no hay tests. Este change **completa, asegura y prueba** el código existente; no construye el módulo desde cero.

## What Changes

- **Cifrado en reposo del email del alumno (AES-256).** `EntradaPadron.email` pasa de `String` plano a un par `email_hash` (búsqueda determinística) + `email_enc` (ciphertext AES-256-GCM), espejando exactamente el patrón de `Usuario` (`encrypt` / `hash_email_for_search` con `aad_suffix`). Incluye migración `021` que cifra las filas existentes. **BREAKING** (forma de la columna y de la fila persistida).
- **Permiso RBAC `padron:vaciar`.** Se declara explícitamente en el catálogo de permisos (hoy *vaciar* reusa indebidamente `padron:importar`) y se asigna a los roles correspondientes. El endpoint de vaciado pasa a exigir `padron:vaciar` y a aplicar las reglas de pertenencia: PROFESOR solo puede vaciar versiones cargadas por él mismo (`version.cargado_por == current_user.id`); COORDINADOR puede vaciar cualquier versión (global).
- **Corrección de auditoría.** Se introduce el código de acción `PADRON_VACIAR` en el vocabulario de `audit_emit` y se corrige `vaciar_datos`, que hoy emite erróneamente `PADRON_CARGAR`. La carga sigue emitiendo `PADRON_CARGAR`. Ambos eventos quedan registrados append-only.
- **Suite de tests (Strict TDD).** Se cubre con tests rojos→verdes→triangulación: versionado (activar una versión desactiva la previa), import xlsx (preview + confirmación atómica), import csv (fallback de encoding UTF-8→Latin-1), entrada sin `usuario_id` (alumno sin cuenta), autorización de vaciado por rol/pertenencia, aislamiento multi-tenant, y manejo de Moodle WS con cliente mockeado ante HTTP 502.

**Fuera de alcance (explícito):** el campo `actividades` de `VersionPadron` permanece `[]` (se completa en C-10); la sincronización nocturna automática contra Moodle WS es trabajo futuro.

## Capabilities

### New Capabilities
- `padron-ingesta`: ingesta versionada del padrón desde xlsx/csv — preview sin persistir, confirmación atómica (versión + entradas), activación de versión que desactiva la previa, fallback de encoding, y entradas con o sin `usuario_id`.
- `padron-email-cifrado`: el email del alumno se almacena cifrado en reposo (AES-256) con hash determinístico para matching, nunca en texto plano; las filas existentes se migran.
- `padron-vaciar-autorizacion`: la operación de vaciado exige el permiso `padron:vaciar` y respeta pertenencia — PROFESOR solo sus propias versiones, COORDINADOR cualquiera (global).
- `padron-auditoria`: las operaciones de carga y vaciado registran eventos de auditoría append-only (`PADRON_CARGAR`, `PADRON_VACIAR`) sin filtrar PII.
- `padron-moodle-sync`: la sincronización contra Moodle WS degrada de forma controlada (HTTP 502 → sugerir importación manual) sin romper el flujo.

### Modified Capabilities
<!-- Sin cambios de requerimientos a nivel spec sobre capacidades preexistentes; el cifrado reusa el patrón de pii-encryption sin alterar su contrato. -->

## Impact

- **Modelos:** `backend/app/models/padron.py` (`EntradaPadron`: `email` → `email_hash` + `email_enc`).
- **Repositorio:** `backend/app/repositories/padron.py` (cifrado al crear entradas, descifrado al leer; chequeo de pertenencia en vaciado).
- **Servicios:** `backend/app/services/padron.py` (auditoría correcta de carga/vaciado, autorización de vaciado por rol/pertenencia).
- **Router:** `backend/app/routers/padrones.py` (declarar `padron:vaciar` en el endpoint de vaciado; corregir el uso del guard RBAC).
- **RBAC:** catálogo de permisos — alta de `padron:vaciar`.
- **Auditoría:** `backend/app/core/audit.py` (alta del código `PADRON_VACIAR`).
- **Migraciones:** nueva `021_padron_email_cifrado.py` (cambio de schema + migración de datos existentes) y nueva migración de permiso `padron:vaciar`.
- **Tests:** nuevos tests de padrón (versionado, import xlsx/csv, sin usuario, vaciado por rol, multi-tenant, Moodle 502).
- **Dependencias:** ninguna nueva; reusa `app.core.security.crypto`, `app.core.security.hashing`, `app.core.audit`, `app.integrations.moodle_ws`.
