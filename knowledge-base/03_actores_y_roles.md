# 03 — Actores y Roles

## Actores del sistema

### A1 — PROFESOR (docente regular)
- **Rol confirmado**: visible en tabla de "Mis equipos" con valor `PROFESOR`.
- **Acceso típico**: index.php, mis_equipos, mis_guardias, mis_tareas, encuentros, perfil.
- **Restricciones observadas**: `admin_mail_approval.php` redirige, `salarios.php` → No autorizado.

### A2 — COORDINADOR
- **Rol confirmado**: visible en tabla de "Mis equipos" con valor `COORDINADOR`.
- **Diferencia con PROFESOR**: en `admin_asignaciones.php` hay campo `responde_legs[]` → un coordinador es quien "responde" por uno o más profesores.
- **Suposición:** accede al menú "Gestión" completo (Profesores, Asignaciones, Carreras, Cohortes, etc.).

### A3 — ADMIN (flag booleano `is_admin`)
- **Evidencia**: en `admin_profesores.php` hay checkbox `is_admin` separado del rol.
- **Lectura**: es un atributo ortogonal al rol académico — un profesor o coordinador puede o no ser admin del sistema.
- **Privilegios inferidos**: ABM de profesores, edición de salarios, aprobación de mails masivos.

### A4 — ADMIN FINANCIERO (inferido)
- **No es un rol visible** explícitamente, pero `salarios.php` requiere autorización adicional incluso para un coordinador.
- **Suposición:** existe un permiso fino sobre el módulo de Salarios/Liquidaciones, posiblemente vinculado a `is_admin` o a un flag adicional.

### A5 — TUTOR (CONFIRMADO ✅)
- **Evidencia confirmada**: `salarios.php` muestra el catálogo cerrado de roles en los selects `base_rol` y `plus_rol`: `ALL, PROFESOR, TUTOR, NEXO, COORDINADOR`.
- **Salario base detectado**: TUPAD pagó $420.000/mes a TUTOR desde 2026-02-01 (al momento del análisis).
- **Diferencia con PROFESOR**: rol intermedio, posiblemente auxiliares/ayudantes con responsabilidades de seguimiento y guardias, menor remuneración que PROFESOR ($560.000).

### A8 — NEXO (CONFIRMADO ✅ — descubierto en segunda pasada)
- **Evidencia confirmada**: opción del select en `salarios.php` + sección dedicada en `liquidaciones.php`: *"Roles NEXO (se muestran aparte, pero suman al total y al resumen por docente)"*.
- **Salario base detectado**: $660.000/mes (más que PROFESOR, menos que COORDINADOR).
- **Lectura semántica**: posiblemente rol de **enlace/articulación territorial o académica** — un puente entre la institución y un grupo de docentes o alumnos.
- **Tratamiento contable especial**: aparece en una tabla aparte en la liquidación pero suma al total general.

### A6 — ALUMNO (sujeto, NO usuario)
- **No tiene UI propia** en este sistema.
- Aparece como **destinatario** de mails, como **registro** en padrones, y como **objeto observado** en monitores.
- Toda interacción real del alumno ocurre en Moodle.

### A7 — USUARIO ANÓNIMO
- **No tiene acceso**: la única ruta "pública" inferida es la de login. Ningún `.php` recorrido funcionó sin sesión.

## Tabla RBAC (inferida)

| Pantalla | PROFESOR | COORDINADOR | ADMIN (is_admin) | ADMIN FINANCIERO |
|----------|----------|-------------|------------------|------------------|
| `index.php` (Procesos Moodle) | ✅ propia | ✅ propia | ✅ | ✅ |
| `coloquios/index.php` | ✅ | ✅ | ✅ | ✅ |
| `monitor_evalia.php` (vista tutor) | ✅ | ✅ | ✅ | ✅ |
| `admin_monitor_evalia.php` (vista admin) | ❓ | ✅ | ✅ | ✅ |
| `admin_coloquios.php` | ❓ | ✅ | ✅ | ✅ |
| `admin.php` (Panel interacciones) | ❓ | ✅ | ✅ | ✅ |
| `mis_equipos.php` | ✅ propio | ✅ propio | ✅ | ✅ |
| `encuentros.php` | ✅ | ✅ | ✅ | ✅ |
| `mis_guardias.php` | ✅ propias | ✅ | ✅ | ✅ |
| `mis_tareas.php` | ✅ propias | ✅ | ✅ | ✅ |
| `admin_reportes.php` (Equipos) | ❓ | ✅ | ✅ | ✅ |
| `admin_profesores.php` | ❌ | ✅ | ✅ | ✅ |
| `admin_asignaciones.php` | ❌ | ✅ | ✅ | ✅ |
| `admin_monitor.php` (Monitor Alumnos) | ❓ | ✅ | ✅ | ✅ |
| `admin_carreras.php` | ❌ | ✅ | ✅ | ✅ |
| `admin_cohortes.php` | ❌ | ✅ | ✅ | ✅ |
| `programas_materias.php` | ❌ | ✅ | ✅ | ✅ |
| `fechas_parciales.php` | ❌ | ✅ | ✅ | ✅ |
| `admin_monitor_general.php` (Monitor Atrasos) | ❓ | ✅ | ✅ | ✅ |
| `admin_avisos.php` | ❌ | ✅ | ✅ | ✅ |
| `admin_mail_approval.php` | 🔒 redirect | ❓ | ✅ | ✅ |
| `admin_tareas.php` | ❌ | ✅ | ✅ | ✅ |
| `liquidaciones.php` | ❌ | ❌ | ✅ (super-admin) | ✅ |
| `salarios.php` | 🔒 No autorizado | 🔒 | ✅ (super-admin) | ✅ |
| `admin_facturas.php` | ❌ | ❌ | ✅ (super-admin) | ✅ |
| `admin_mail_approval.php` | 🔒 redirect | 🔒 redirect | 🔧 redirige si cola vacía | ✅ si hay items |
| `perfil.php` | ✅ propio | ✅ propio | ✅ | ✅ |
| `logout.php` | ✅ | ✅ | ✅ | ✅ |

Leyenda:
- ✅ = acceso confirmado
- ❌ = sin acceso (inferido)
- ❓ = no validado (no se probó con el rol exacto)
- 🔒 = redirección o "No autorizado" confirmado
- "propia/propio" = solo ve sus propios datos, no globales

> **Nota**: el usuario logueado durante el análisis (Cortez Alberto) tiene rol mixto **COORDINADOR + PROFESOR** según su tabla "Mis equipos", lo cual le da casi todos los accesos excepto los dos restringidos.

## Modelo de permisos detectado

### 1. Rol académico (catálogo cerrado, CONFIRMADO en `salarios.php`)
Catálogo cerrado real de roles del sistema (select `base_rol`):
- `ALL` (valor especial: aplica a todos los roles, usado en grilla salarial)
- `PROFESOR`
- `TUTOR`
- `NEXO`
- `COORDINADOR`

### 2. Flag `is_admin` (booleano)
- Atributo ortogonal en `admin_profesores.php`.
- Activa el acceso a las pantallas administrativas del sistema.

### 3. Permisos por módulo (inferido)
- Existe un nivel fino adicional para Salarios y Aprobación de Mails — el simple flag `is_admin` no parece bastar (o el usuario observado no lo tiene activo).

### 4. Vigencia temporal
- Cada asignación de docente tiene `desde` y `hasta` (fechas) y un `Estado` (Vigente / vencida).
- Las cohortes también tienen `vig_desde` y `vig_hasta`.
- **Regla inferida**: los permisos efectivos de un docente sobre una materia están condicionados por la vigencia de su asignación.

## Rutas no autenticadas

Solo se infiere una: **login** (probablemente `login.php` o similar, no recorrida porque el usuario ya estaba logueado al inicio).

→ Ver [10_preguntas_abiertas.md](10_preguntas_abiertas.md#PA-04) para validar.
