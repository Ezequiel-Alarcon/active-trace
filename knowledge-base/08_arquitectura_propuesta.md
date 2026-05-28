# 08 — Arquitectura

> Este archivo documenta la **arquitectura observable** (no propuesta) — refleja decisiones ya tomadas en el sistema en producción. Útil para reverse-engineer, no para diseño nuevo.

## Patrón arquitectónico

**MPA (Multi-Page Application) clásico de PHP**, sin framework SPA detectado. Cada `.php` es un endpoint independiente que mezcla:
- Acceso a datos
- Lógica de negocio
- Render HTML
- Manejo de POST con validación CSRF

No se observa separación MVC formal en URLs — es probable que internamente el código tenga capas, pero la URL es plana.

## Convenciones de routing observadas

```
/evalia/                              ← raíz de la suite
├── mood/                             ← módulo principal (este KB)
│   ├── index.php                     ← home + procesos Moodle del docente
│   ├── admin.php                     ← panel de interacciones
│   ├── perfil.php                    ← perfil + inbox personal
│   ├── logout.php                    ← cierre de sesión
│   │
│   ├── mis_equipos.php               ← vista propia: equipos
│   ├── mis_guardias.php              ← vista propia: guardias
│   ├── mis_tareas.php                ← vista propia: tareas
│   ├── encuentros.php                ← encuentros (propio + admin via tabs)
│   ├── monitor_evalia.php            ← vista tutor: monitor EVALIA
│   │
│   ├── admin_profesores.php          ← ABM profesores
│   ├── admin_asignaciones.php        ← asignación masiva
│   ├── admin_monitor.php             ← monitor alumnos (admin)
│   ├── admin_monitor_evalia.php      ← vista admin: monitor EVALIA
│   ├── admin_monitor_general.php     ← monitor general de actividades
│   ├── admin_carreras.php            ← ABM carreras
│   ├── admin_cohortes.php            ← ABM cohortes
│   ├── admin_avisos.php              ← ABM avisos
│   ├── admin_tareas.php              ← admin tareas
│   ├── admin_reportes.php            ← reportes de equipos / clonado
│   ├── admin_coloquios.php           ← admin coloquios
│   ├── admin_mail_approval.php       ← aprobación de mails (rol restringido)
│   │
│   ├── programas_materias.php        ← programas (PDF)
│   ├── fechas_parciales.php          ← fechas parciales/TP/coloquios
│   │
│   ├── liquidaciones.php             ← liquidaciones (cohorte × mes)
│   ├── salarios.php                  ← grilla salarios (Base+Plus, super-admin)
│   ├── admin_facturas.php            ← ABM facturas de monotributistas (super-admin)
│   │
│   └── coloquios/                    ← sub-módulo coloquios
│       ├── index.php                 ← dashboard coloquios
│       ├── importar.php              ← importar alumnos a coloquios
│       └── convocatoria_form.php     ← crear nueva evaluación
│
└── corrector/                        ← módulo externo Correct-IA (no documentado)
    └── index.php
```

## Patrones de formulario observados

### 1. Self-post con discriminador
Casi todos los forms hacen POST a `(self)` con un campo hidden `action` o `accion` que discrimina la operación:

```html
<form method="post">
  <input type="hidden" name="csrf" value="...">
  <input type="hidden" name="accion" value="crear">  <!-- o "editar", "eliminar" -->
  <input type="hidden" name="id" value="...">
  ...
  <button type="submit">Guardar</button>
</form>
```

### 2. Tokens CSRF universales
Todos los POST llevan `csrf` token oculto. **Suposición:** el token se valida en server-side antes de procesar.

### 3. Filtros GET con submit
Los filtros se aplican vía GET (no AJAX) para preservar URL compartibles:

```
?materia_id=3&carrera=TUPAD&cohorte=MAR-2026&estado=Vigente
```

### 4. Hidden inputs redactados
El accessibility tree muestra `[value redacted]` en hidden inputs — el sistema marca esos campos como sensibles (tokens, IDs, etc.) para evitar exposición en herramientas de scraping/automation. Probablemente atributo `data-redact` o similar.

## Patrones de UI

- **Modales para acciones secundarias**: "Previsualización del email", "Cómo exportar y subir los Excel", "Análisis de notas finales", "Lista de alumnos".
- **Tabs en una sola página**: "Mi equipo / Monitoreo / Mail" en `mis_equipos.php`, "Mis encuentros / Calendario / Vista admin" en `encuentros.php`.
- **Cards colapsables**: cada sección tiene botón "Colapsar/expandir".
- **Status spinners**: loaders "Cargando…" y "Procesando solicitud" estandarizados.
- **Bootstrap-like classes**: `card-header`, `btn`, `form-select`, `nav-link` — sugiere Bootstrap 4 o 5.

## Seguridad

| Medida | Evidencia |
|--------|-----------|
| CSRF token por POST | Campo `csrf:hidden` en todos los forms |
| Auth basada en sesión | `logout.php` destruye cookie |
| Authz por ruta | `admin_mail_approval.php` redirige, `salarios.php` → No autorizado |
| Audit log | Cada acción con IP + User-Agent en `admin.php` |
| Hidden values redactados | `[value redacted]` en accessibility tree |
| Scope isolation | "Vaciar datos" no afecta a otros profesores |

**Falencias observables**:
- No se observa rate limiting visible.
- No se observan flags de seguridad de cookies (visibles desde el navegador, no desde la UI).
- El log de auditoría está limitado a "máx. 200" recientes — probablemente más en DB pero la UI no permite paginar atrás.

## Variables de entorno / configuración (inferidas)

| Variable | Propósito inferido |
|----------|-------------------|
| DB connection | MySQL/MariaDB host, user, pass, dbname |
| SMTP / mail backend | Server de envío de mails (con queue) |
| Storage path | Disco donde se almacenan los PDF de `programas_materias.php` |
| App URL base | `https://olsoft.online/evalia/mood/` |
| Session secret | Para firmar cookies de sesión |
| CSRF secret | Para firmar tokens CSRF |
| Moodle column hints | Sufijos como `(Real)` y valores como `"Satisfactorio"` |

**Suposición:** todos en archivo `.env` o `config.php` server-side, no expuesto en UI.

## Integraciones de salida

| Integración | Tipo | Observaciones |
|-------------|------|---------------|
| Excel (export) | Generación de `.xlsx` con PHPExcel | Múltiples botones "Exportar Excel" |
| Moodle (import) | Lectura `.xlsx` / `.csv` | Convención de columnas (Real) |
| Google Meet | Solo URL (link manual) | No hay API integration |
| Mail (SMTP) | Worker async con queue | Estados Pend/Send/OK/Fail/Canc |
| HTML snippet | Output para pegar en Moodle | En encuentros + fechas_parciales |

## Esquema lógico simplificado de capas (inferido)

```
┌─────────────────────────────────────────┐
│   Browser (Bootstrap + vanilla JS)      │
└────────────────┬────────────────────────┘
                 │ HTTP(S) — sesión PHP
┌────────────────▼────────────────────────┐
│   PHP MPA (Apache/Nginx)                │
│   - rutas .php = endpoints              │
│   - render server-side                  │
│   - CSRF check                          │
│   - Authz check por rol/route           │
├─────────────────────────────────────────┤
│   Lógica de negocio (capa interna)      │
│   - parser PHPExcel                     │
│   - umbral / clasificación de notas     │
│   - generación HTML para Moodle         │
│   - cálculo de liquidaciones            │
│   - generación de mails personalizados  │
├─────────────────────────────────────────┤
│   Persistencia (MySQL/MariaDB)          │
│   - tablas: profesores, alumnos,        │
│     calificaciones, asignaciones,       │
│     emails, audit_log, ...              │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Worker de mails (async)               │
│   - cola Pend → Send → OK/Fail/Canc     │
│   - integración SMTP / API mail         │
└─────────────────────────────────────────┘
```

## Decisiones de diseño visibles

1. **Stack PHP clásico sin framework SPA**: prioriza velocidad de desarrollo + bajo costo de hosting, a costa de DX moderno y reuso.
2. **Importación manual de Moodle**: no hay API directa, lo cual sugiere que Moodle del cliente no expone APIs o que se prefiere control humano sobre cada import.
3. **Aprobación humana antes de mails masivos**: hay un workflow de aprobación → indica importancia del cuidado reputacional / spam compliance.
4. **Auditoría exhaustiva**: el sistema asume contexto regulado o auditado (ambiente educativo institucional).
5. **Catálogos duplicados de materias**: ver [10_preguntas_abiertas.md PA-01](10_preguntas_abiertas.md#pa-01) — posible deuda técnica.

## Convenciones de codificación inferidas

| Convención | Ejemplo |
|------------|---------|
| URLs en lowercase con snake_case | `admin_monitor_evalia.php` |
| Parámetros GET con `_id` para FKs | `?materia_id=3` |
| Campos de form en snake_case | `csrf, materia_id, vig_desde` |
| Acciones POST con hidden `accion` | `accion=editar` |
| Filtros con prefijo `f_` | `f_mat, f_scope, f_cohId, f_act` |
| Selects múltiples con `[]` | `legs[], comisiones[], responde_legs[]` |
| Hash booleano | "Activa" / "Inactiva" (texto) en UI; bool en DB (supuesto) |

## Footprint operacional

- **Producción activa**: confirmado por volumen de datos (278 emails OK por docente × materia, 250 guardias, 443 tareas, 14 programas).
- **Time zone**: fechas en formato `YYYY-MM-DD HH:MM:SS`, días en español ("Miércoles") — Argentina.
- **i18n**: español rioplatense únicamente. No hay selector de idioma.
- **Responsive**: viewport 1693x770 testeado OK; menú con botón "Menú" sugiere colapso mobile (no validado).
