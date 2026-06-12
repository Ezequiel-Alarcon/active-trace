# Proposal: C-09 — Padrón e Ingesta desde Moodle

## 1. Problem Statement

El sistema necesita consumir datos del LMS (Moodle) para funcionar como capa de orquestación académica. Actualmente no tiene forma de importar el padrón de alumnos por materia ni sincronizar actividades y participantes. Sin esto, no existe base干净 para los módulos de calificaciones (C-10), análisis de atrasados (C-11) ni comunicaciones (C-12).

## 2. What We Are Building

Módulo de ingestión de datos desde archivos exportados del LMS y sincronización con Moodle Web Services:

- **Modelo versionado** `VersionPadron` + `EntradaPadron`: cada carga crea una nueva versión; solo una activa por materia×cohorte.
- **Importación de padrón** desde `.xlsx`/`.csv` con vista previa antes de confirmar.
- **Cliente de Moodle Web Services** (`moodle_ws.py`) para sync de usuarios/actividades con fallback manual cuando Moodle no está disponible.
- **Vaciado de datos** de materia (F1.5, RN-04) con auditoría.
- **API REST** con RBAC: `padron:importar` para PROFESOR/COORDINADOR.

## 3. Why This Approach

- **Versionado en lugar de upsert destructivo**: preserva historial para auditoría y permite rollback. La KB dice "upsert destructivo" (F1.3) pero el modelo E6 dice versionado — prevalece el modelo E6 por ser más robusto.
- **Fallback manual**: si Moodle WS falla (502), el usuario puede importar manualmente. Esto evita bloquear el flujo académico.
- **Cliente dedicado**: separación clara entre lógica de dominio e integración externa, siguiendo ADR-009 (Clean Architecture).

## 4. Out of Scope

- Importación de calificaciones (C-10)
- Detección de entregables sin nota (F1.2 — se hace en C-10)
- Creación de usuarios en Moodle
- Sincronización bidireccional completa

## 5. Dependencies

- **C-07** (`usuarios-y-asignaciones`): necesita los modelos `Usuario` y `Asignacion` para resolver `usuario_id` en `EntradaPadron`.
- **C-05** (`audit-log`): necesita el helper/decorator de auditoría para `PADRON_CARGAR`.
- **C-04** (`rbac`): necesita el sistema de permisos para `padron:importar`.

## 6. Success Criteria

1. Importar `.xlsx` con 500+ filas en < 5 segundos (preview) y confirmar en < 10s total.
2. Solo una versión activa por `(materia_id, cohorte_id)` — activar nueva desactiva anterior.
3. Entrada sin `usuario_id` (alumno sin cuenta) se persiste y se resuelve después.
4. Fallo de Moodle WS devuelve `502` con mensaje de fallback manual, no crash.
5. Audit log registra `PADRON_CARGAR` con `filas_afectadas`.
6. Tests: versionado, import xlsx/csv, entrada sin usuario, aislamiento tenant, mock Moodle + fallback 502.