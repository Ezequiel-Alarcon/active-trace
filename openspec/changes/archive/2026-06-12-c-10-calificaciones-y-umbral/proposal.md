# C-10: Calificaciones y Umbral

## Why

Moodle no almacena notas de forma estructurada queryable desde fuera, y el sistema actual carece de un modelo de calificaciones que permita analizar rendimiento, detectar atrasos y exportar datos a Finanzas. Se necesita un modelo `Calificacion` con umbral configurable por materia/asignación para determinar aprobación y un flujo de importación en dos pasos (preview + confirmar) que aproveche los datos ya ingestados en C-09.

## What Changes

- Nuevo modelo `Calificacion` con campos: `materia_id`, `usuario_id`, `asignacion_id`, `nota` (numérica/texto/conjunto), `origen` (Importado/Manual), `version_padron_id` opcional
- Nuevo modelo `UmbralMateria` con `umbral_pct` por `asignacion_id` (defecto 60%)
- Importación de calificaciones LMS en 2 pasos: preview sin persistir → confirmar (persistir y auditar)
- Importación de reporte de finalización (TPs sin nota) → `nota = null`, `origen = Importado`
- Lógica de derivación `aprobado` en 3 casos: numérica vs umbral, textual vs conjunto, sin_nota → False
- API endpoints para CRUD de calificaciones y configuración de umbrales
- Permiso `calificaciones:importar` ya existe en catálogo (seed 002)

## Capabilities

### New Capabilities

- `calificacion-import`: Importación de calificaciones LMS con preview en dos pasos (sin persistir → confirmar)
- `umbral-materia`: Modelo y API para configurar umbral de aprobación por materia/asignación
- `calificacion-modelo`: Modelo de datos `Calificacion` con auditoría de cambios
- `calificacion-aprobado-derivacion`: Lógica de derivación `aprobado` en 3 casos según tipo de nota

### Modified Capabilities

- (ninguno — no cambia requisitos de specs existentes)

## Impact

- **Nuevo módulo**: `src/domain/calificaciones/` (models, schemas, services, repositories)
- **Nuevo modelo DB**: `calificacion`, `umbral_materia` (2 migraciones Alembic)
- **API endpoints**: `GET/POST /api/calificaciones`, `GET /api/calificaciones/preview`, `POST /api/calificaciones/confirmar`, `GET/PUT /api/umbral-materia`
- **Dependencias**: C-09 (padron-ingesta-moodle) — usa `VersionPadron`, `Materia`, `Usuario`
- **Permisos**: `calificaciones:importar` (ya existe en seed), `calificaciones:ver`