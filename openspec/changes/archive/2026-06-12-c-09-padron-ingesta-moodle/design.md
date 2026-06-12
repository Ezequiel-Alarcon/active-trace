## Context

El sistema `activia-trace` necesita consumir datos del LMS (Moodle) como fuente de verdad para el flujo académico. El módulo C-09 implementa la ingesta de padrón de alumnos y la integración con Moodle Web Services.

**Estado actual**: No existe ningún modelo ni endpoint para ingestión de datos del LMS. Los modelos `VersionPadron` y `EntradaPadron` están definidos en la KB (E6) pero no implementados.

**Restricciones**:
- Multi-tenancy row-level: todo query filtra por `tenant_id`.
- PII cifrado en reposo: `email` de alumno es `[cifrado]`.
- Regla de oro: identidad del usuario desde JWT, nunca de parámetros.
- Soft delete siempre.

## Goals / Non-Goals

**Goals:**
- Modelo versionado de padrón: `VersionPadron` + `EntradaPadron` por `(materia_id, cohorte_id)`.
- Importación de `.xlsx`/`.csv` con preview antes de confirmar.
- Cliente `moodle_ws.py` para sync de usuarios/actividades con fallback manual.
- Vaciado de datos de materia (F1.5) con auditoría `PADRON_CARGAR`.
- RBAC: `padron:importar` para PROFESOR/COORDINADOR.

**Non-Goals:**
- Importación de calificaciones (C-10).
- Creación de usuarios en Moodle.
- Sincronización bidireccional completa.
- Detección de entregables sin nota (C-10).

## Decisions

### D1: Modelo versionado con `activa` boolean

**Decisión**: `VersionPadron` tiene campo `activa: bool`. Solo una activa por `(materia_id, cohorte_id)` en simultáneo.

**Alternativa**: usar `fecha_activacion` y tomar la más reciente. **Rechazada** porque requiere lógica de "la más reciente" en cada query y no permite desactivar sin borrar.

**Implementación**: al activar una versión, un servicio atómico desactiva las demás de la misma `(materia_id, cohorte_id)` dentro de una transacción.

### D2: Cliente Moodle WS como módulo dedicado

**Decisión**: `integrations/moodle_ws.py` es un clientehttpx con reintento y mapeo de errores a `502`.

**Diseño**:
- Clase `MoodleWSClient` con métodos `get_users()`, `get_activities()`, `sync_enrollments()`.
- Timeouts configurables (default 30s).
- Retry con exponential backoff (3 intentos).
- Error `MoodleWSError` → mapeado a `502 Bad Gateway` en el router.
- Cuando Moodle no responde, el usuario puede usar importación manual `.xlsx`/`.csv`.

### D3: Importación en dos pasos (preview → confirmar)

**Decisión**: el flujo de importación es:
1. `POST /api/padrones/preview` — recibe archivo, parsea, devuelve rows detectados sin persistir.
2. `POST /api/padrones` — persiste la versión nueva y sus entradas.

**Ventaja**: el usuario puede corregir errores de formato antes de confirmar. Evita cargas parciales o incorrectas.

### D4: `usuario_id` nullable en `EntradaPadron`

**Decisión**: `EntradaPadron.usuario_id` es `UUID | None`. Un alumno sin cuenta se persiste con `usuario_id = NULL` y se resuelve cuando el alumno se registra.

**Motivación**: permite cargar el padrón antes de que todos los alumnos tengan cuenta en el sistema. El campo `email` (marcado como `[cifrado]`) permite hacer el matching después.

### D5: Archivo temporal en disco, no en memoria

**Decisión**: el archivo subido se guarda en `/tmp/activia-trace/uploads/` con nombre efímero, se procesa y se elimina.

**Alternativa**: mantener en memoria con `UploadedFile`. **Rechazada** porque archivos grandes (>10MB) pueden agotar memoria en requests concurrentes.

**Seguridad**: el path es opaco (UUID), no predecible. Archivos `.exe`, `.php`, etc. se rechazan por extensión.

## Risks / Trade-offs

- **[Risk]Archivo grande (>50MB) satura el worker** → [Mitigation] Validar tamaño en el endpoint (max 50MB) y devolver `413 Request Entity Too Large`.
- **[Risk]CSV con encoding diferente (Latin-1)** → [Mitigation] Probar `utf-8` primero, fallback a `latin-1`, error claro si falla.
- **[Risk]Moodle lento o unreachable** → [Mitigation] Timeout de 30s, retry 3 veces, fallback a `502` con sugerencia de importación manual.
- **[Risk]Email de alumno no es único entre plataformas** → [Mitigation] Se almacena el email tal cual viene del LMS; el matching con `Usuario` se hace por `email` cuando el alumno se registra.

## Migration Plan

1. Crear migración `007: version_padron, entrada_padron`.
2. Crear modelos, schemas, repositories, services, routers.
3. Crear cliente `moodle_ws.py` con interface mínima.
4. Escribir tests de integración con mock de Moodle WS.
5. Deploy: sin breaking changes (módulo nuevo).

## Open Questions

- **Q1**: ¿El `comision` de `EntradaPadron` es un texto libre o se mapea a una entidad del sistema? Por ahora texto libre; se puede extender.
- **Q2**: ¿La sync nocturna de Moodle se implementa en este change o en C-12 (worker)? Queda como interface en `moodle_ws.py`; la invocación scheduled viene con C-12.