# Base de Conocimiento — PulseUPs® / Evalia (TUPAD)

Esta KB fue generada por **análisis directo de la herramienta en producción** en `https://olsoft.online/evalia/mood/index.php` el 2026-05-28, recorriendo pantalla por pantalla con un usuario logueado en rol PROFESOR + COORDINADOR.

## Sistema documentado

- **Nombre comercial**: PulseUPs® — "Gestor de Rendimiento Académico & Recordatorios" (by OscarLondero®)
- **Subtítulo**: "Gestión académica"
- **Producto base detectado**: `evalia/mood/` (módulo Moodle de la suite Evalia)
- **Carrera activa única**: TUPAD — Tecnicatura Universitaria en Programación a Distancia
- **Lenguaje backend**: PHP (todas las rutas son `.php`)
- **Hosting**: olsoft.online (Argentina, por regionales detectadas)

## Cómo está organizada

| # | Archivo | Contenido |
|---|---------|-----------|
| 01 | [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance, fuera de alcance |
| 02 | [02_descripcion_general.md](02_descripcion_general.md) | Stack inferido, arquitectura, integraciones (Moodle, Meet, mail) |
| 03 | [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, tabla RBAC, rutas restringidas detectadas |
| 04 | [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entidades inferidas, ERD, relaciones |
| 05 | [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas codificadas (RN-XX) por dominio |
| 06 | [06_funcionalidades.md](06_funcionalidades.md) | Funcionalidades organizadas por épica |
| 07 | [07_flujos_principales.md](07_flujos_principales.md) | Flujos extremo a extremo (importar Moodle, mensajería, etc.) |
| 08 | [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones observados, estructura de URLs, seguridad |
| 09 | [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones de diseño visibles + supuestos inferidos |
| 10 | [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias detectadas + preguntas para validar con el dueño |
| 11 | [11_historias_de_usuario.md](11_historias_de_usuario.md) | 47 historias de usuario (formato Connextra + CA), cruzadas con features y reglas |

## Historial de actualizaciones

| Fecha | Cambio |
|-------|--------|
| 2026-05-28 (v0.1) | Generación inicial — análisis con usuario rol COORDINADOR+PROFESOR (Cortez Alberto) |
| 2026-05-28 (v0.2) | **Segunda pasada con super-admin** (Rodriguez Georgina vía `?leg=1`) — accedidas `salarios.php`, `admin_facturas.php`, `liquidaciones.php` con datos reales. Cerradas PA-02 y PA-06. Descubierto rol NEXO + nueva pantalla `admin_facturas.php`. Agregadas RN-31..41, E20..23, F10.5/F10.6, HU-48/49, PA-21..25 |

## Importante — confiabilidad de la información

Esta KB se construyó por **observación de UI**, sin acceso al código fuente, base de datos ni documentación interna. Cada afirmación entra en una de estas categorías:

- **Hecho confirmado**: visible literalmente en pantalla (etiquetas, valores, columnas).
- **Inferencia razonable**: deducido del comportamiento observable.
- **Suposición**: marcado con `**Suposición:**` — requiere validación.

Las inconsistencias y dudas pendientes están consolidadas en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

## Próximos pasos sugeridos

1. Revisar [10_preguntas_abiertas.md](10_preguntas_abiertas.md) con el responsable del producto.
2. Validar el ERD inferido en [04_modelo_de_datos.md](04_modelo_de_datos.md) contra el esquema real.
3. Acceder con un usuario rol "Admin total" para documentar `admin_mail_approval.php` y `salarios.php`.
4. Documentar el submódulo externo **Correct-IA** (`/evalia/corrector/`) — fuera del alcance de esta pasada.
