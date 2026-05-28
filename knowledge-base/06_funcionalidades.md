# 06 — Funcionalidades

Funcionalidades del sistema agrupadas por **épica**. Cada feature está vinculada a la pantalla donde se observa.

---

## Épica 1 — Ingesta de Datos desde Moodle

### F1.1 — Importar Excel de calificaciones por materia
- **Dónde**: `index.php` sección 1.a "Calificaciones - Subir Excel (.xlsx)"
- **Quién**: PROFESOR
- **Flujo**:
  1. Selecciona materia
  2. Sube archivo `.xlsx` exportado desde Moodle
  3. Click "Generar preview"
  4. Seleccionar qué actividades del Excel analizar
- **Reglas aplicadas**: [RN-01](05_reglas_de_negocio.md#rn-01), [RN-02](05_reglas_de_negocio.md#rn-02)

### F1.2 — Importar reporte de finalización (para detectar TP sin corregir)
- **Dónde**: `index.php` sección 1.b "Correcciones · Subir reporte de finalización"
- **Quién**: PROFESOR
- **Acepta**: `.xlsx` o `.csv/.tsv` tabulado directo de Moodle
- **Output**: tabla "Posibles TPs sin corregir (por actividad)"
- **Reglas aplicadas**: [RN-07](05_reglas_de_negocio.md#rn-07), [RN-08](05_reglas_de_negocio.md#rn-08)

### F1.3 — Importar padrón EVALIA
- **Dónde**: `monitor_evalia.php` sección "Importar padrón desde Moodle (participantes)"
- **Quién**: PROFESOR (de su materia EVALIA) / COORDINADOR (global)
- **Toma**: Nombre, Apellido(s), Dirección de correo, Grupos
- **Comportamiento**: upsert destructivo — reemplaza padrón anterior ([RN-05](05_reglas_de_negocio.md#rn-05))

### F1.4 — Importar listado y actividades (admin)
- **Dónde**: `admin_monitor.php` secciones 1 y 2
- **Quién**: COORDINADOR
- **Flujo bi-step**:
  1. Importar Listado (participantes)
  2. Importar Actividades (calificaciones Moodle)

### F1.5 — Vaciar datos por materia
- **Dónde**: `index.php` botón "Vaciar datos de esta materia"
- **Quién**: PROFESOR
- **Scope**: solo los datos del docente en esa materia ([RN-04](05_reglas_de_negocio.md#rn-04))

---

## Épica 2 — Análisis y Reportes Académicos

### F2.1 — Configurar umbral por materia
- **Dónde**: `index.php` sección "Umbral global"
- **Quién**: PROFESOR
- **Default**: 60% ([RN-03](05_reglas_de_negocio.md#rn-03))

### F2.2 — Visualizar estudiantes atrasados
- **Dónde**: `index.php` sección 3
- **Definición**: alumnos con actividades faltantes O nota < umbral ([RN-06](05_reglas_de_negocio.md#rn-06))

### F2.3 — Ranking de aprobadas
- **Dónde**: `index.php` sección 4
- **Output**: ranking por cantidad de actividades aprobadas
- **Filtro**: solo alumnos con ≥1 aprobada ([RN-09](05_reglas_de_negocio.md#rn-09))

### F2.4 — Reportes rápidos por materia
- **Dónde**: `index.php` sección 2.a
- **Estado inicial**: "Aún no hay datos importados o no hay actividades seleccionadas."

### F2.5 — Notas finales (agrupación para Excel)
- **Dónde**: `index.php` sección 2.b
- **Output**: agrupa actividades configuradas en una nota final exportable

### F2.6 — Exportar TPs sin corregir
- **Dónde**: `index.php` botón "Exportar Excel" en sección de TPs sin corregir
- **Output**: archivo Excel descargable

### F2.7 — Monitor general de alumnos (vista admin)
- **Dónde**: `admin_monitor_general.php` ("Monitor de actividades")
- **Filtros**: materia, regional, comisión, búsqueda libre, estado
- **Acciones**: Aplicar, Exportar, Limpiar, "Criterio de clasificación"

### F2.8 — Monitor EVALIA (vista tutor)
- **Dónde**: `monitor_evalia.php`
- **Filtros**: materia, alumno/email/comisión, regional, actividad (con/sin), mínimo de actividad

### F2.9 — Monitor EVALIA (vista admin)
- **Dónde**: `admin_monitor_evalia.php`
- **Filtros adicionales**: rango de fechas

---

## Épica 3 — Comunicación con Alumnos

### F3.1 — Preview del email antes de enviar
- **Dónde**: modal "Previsualización del email" disponible desde varias pantallas
- **Muestra**: Asunto + Cuerpo HTML renderizado
- **Regla**: [RN-16](05_reglas_de_negocio.md#rn-16)

### F3.2 — Envío masivo con cola
- **Workflow**: Pend → Send → OK/Fail/Canc ([RN-15](05_reglas_de_negocio.md#rn-15))
- **Tracking**: visible en `admin.php` tabla "Estado de comunicaciones"

### F3.3 — Aprobación de envíos masivos
- **Dónde**: `admin_mail_approval.php` (rol restringido)
- **Suposición**: cola intermedia donde un admin valida y aprueba envío
- **Regla**: [RN-17](05_reglas_de_negocio.md#rn-17)

### F3.4 — Mensajería interna (inbox del docente)
- **Dónde**: `perfil.php` formulario con `thread_id, mail_id, reply_subject, reply_body, mv_reply_btn`
- **Capacidad**: leer threads, responder mensajes
- **Suposición**: el inbox recibe notificaciones del sistema (avisos, respuestas de alumnos, mensajes de coordinación).

### F3.5 — Avisos del sistema (tablón)
- **Dónde**: `admin_avisos.php` (ABM)
- **Capacidades**: scope (global/materia/cohorte), severity, role_target, vigencia start/end, sort, require_ack
- **Reglas**: [RN-18](05_reglas_de_negocio.md#rn-18), [RN-19](05_reglas_de_negocio.md#rn-19), [RN-20](05_reglas_de_negocio.md#rn-20)

---

## Épica 4 — Gestión de Equipos Docentes

### F4.1 — ABM de profesores
- **Dónde**: `admin_profesores.php`
- **Campos**: legajo, nombre, dni, banco, cbu, alias_cbu, regional, legajo_profesional, estado, is_admin
- **Acciones**: agregar, editar, activar/desactivar

### F4.2 — Mis equipos (vista propia)
- **Dónde**: `mis_equipos.php`
- **Sub-tabs**: Mi equipo, Monitoreo, Mail
- **Filtros**: estado, materia, rol, carrera, cohorte
- **Output**: tabla Carrera | Cohorte | Rol | Comisiones | Vigencia | Estado

### F4.3 — Asignaciones individuales
- **Dónde**: `admin_asignaciones.php` sección "Asignaciones actuales"
- **Filtros**: materia, carrera, cohorte, legajo, profesor, rol, responde

### F4.4 — Asignación masiva
- **Dónde**: `admin_asignaciones.php` sección "Asignación masiva"
- **Permite**: seleccionar múltiples legajos (checkboxes + autocomplete bulkSearch) y asignarlos en bloque a una materia × carrera × cohorte × rol con vigencia
- **Regla**: [RN-30](05_reglas_de_negocio.md#rn-30)

### F4.5 — Clonar equipo docente
- **Dónde**: `admin_reportes.php`
- **Operación**: duplica asignaciones desde origen (materia × carrera × cohorte) a destino
- **Regla**: [RN-12](05_reglas_de_negocio.md#rn-12)

### F4.6 — Modificar vigencia general del equipo
- **Dónde**: `admin_reportes.php`
- **Input**: vigenciaDesdeEquipo, vigenciaHastaEquipo
- **Efecto**: cambia las fechas de TODAS las asignaciones del equipo seleccionado

### F4.7 — Exportar Excel de equipo
- **Dónde**: `admin_reportes.php` botón "Exportar Excel"

---

## Épica 5 — Estructura Académica

### F5.1 — ABM de carreras
- **Dónde**: `admin_carreras.php`
- **Campos**: código, nombre, estado
- **Único valor actual**: TUPAD

### F5.2 — ABM de cohortes
- **Dónde**: `admin_cohortes.php`
- **Campos**: nombre, año, vig_desde, vig_hasta, estado
- **Ejemplos**: MAR-2025, AGO-2025, MAR-2026

### F5.3 — Programas de materias (PDF)
- **Dónde**: `programas_materias.php`
- **Permite**: subir PDF del programa por materia × carrera × cohorte con título
- **Cantidad actual**: 14 programas cargados

### F5.4 — Fechas de parciales / TP / coloquios
- **Dónde**: `fechas_parciales.php`
- **Campos**: materia, tipo (parcial/TP/coloquio), número, fecha, cohorte, título
- **Vistas**: tabla lineal + Calendario de evaluaciones
- **Output extra**: snippet HTML para pegar en Moodle

---

## Épica 6 — Encuentros y Disponibilidad

### F6.1 — Crear slot de encuentro recurrente
- **Dónde**: `encuentros.php` sección "Crear encuentro" modo recurrente
- **Inputs**: materia, hora, día semana, fecha desde, semanas, título, meet
- **Efecto**: genera N instancias automáticamente

### F6.2 — Crear encuentro único
- **Dónde**: `encuentros.php` sección "Crear encuentro" modo único
- **Input**: fecha individual + hora + título + meet

### F6.3 — Editar instancia de encuentro
- **Campos modificables**: estado, meet, video, comentario
- **Suposición**: el video se carga DESPUÉS de realizado el encuentro

### F6.4 — Generar HTML para Moodle
- **Output**: snippet HTML con los slots/instancias listos para pegar en el aula virtual

### F6.5 — Vista admin de encuentros
- **Dónde**: tab "Vista admin" en `encuentros.php`
- **Otros tabs**: Mis encuentros, Calendario, Vista admin

### F6.6 — Registro de guardias
- **Dónde**: `mis_guardias.php`
- **Tabla**: # | Tutor | Materia | Carrera/Cohorte | Día | Horario | Estado | Comentarios | Creada
- **Acción**: exportar Excel
- **Suposición**: el alta de guardia es desde otra pantalla (no se observó form de alta)

---

## Épica 7 — Coloquios

### F7.1 — KPIs de coloquios
- **Dónde**: `coloquios/index.php`
- **Métricas**: Alumnos cargados, Instancias, Reservas activas, Notas registradas

### F7.2 — Importar alumnos a coloquios
- **Dónde**: `coloquios/index.php` botón "Importar alumnos" → `importar.php`

### F7.3 — Nueva evaluación de coloquio
- **Dónde**: `coloquios/index.php` botón "Nueva evaluación" → `convocatoria_form.php`

### F7.4 — Listado de evaluaciones
- **Tabla**: ID | Materia | Instancia | Días disponibles | Convocados | Reservas | Cupos libres | Acciones

### F7.5 — Admin de coloquios
- **Dónde**: `admin_coloquios.php`
- **Sub-secciones**:
  - Evaluaciones de coloquio
  - Registro académico consolidado
  - Agenda de reservas activas

---

## Épica 8 — Workflow de Tareas

### F8.1 — Mis tareas (vista profesor)
- **Dónde**: `mis_tareas.php`
- **Filtro**: contexto (`ctx_id`)
- **Botones**: "Asignar (Profe)", "Admin"

### F8.2 — Asignar tarea (profe → otro profe)
- **Dónde**: botón "Asignar (Profe)" en `mis_tareas.php`
- **Suposición**: permite delegar tareas a otros docentes

### F8.3 — Administrar tareas (coordinación)
- **Dónde**: `admin_tareas.php`
- **Volumen actual**: 443 tareas
- **Filtros**: profesor (asignado), profesor (asignador), materia, estado, búsqueda libre
- **Acción**: cambiar estado + agregar comentario (workflow asincrónico)

---

## Épica 9 — Auditoría y Métricas

### F9.1 — Panel de interacciones
- **Dónde**: `admin.php`
- **Sub-vistas**:
  - Acciones por día
  - Estado de comunicaciones (Pend/Send/OK/Fail/Canc por docente)
  - Interacciones por docente & materia (Desempeño/Preview/Import/Env./Reset/Umbral/Emails/Batches)
  - Últimas acciones (log, máx. 200)
- **Filtros**: from/to, materia, legajo, "inactive"

### F9.2 — Log de auditoría completo
- **Dónde**: tabla "Últimas acciones" en `admin.php`
- **Columnas**: Fecha | Legajo | Materia | Acción | Rows | IP | User-Agent
- **Reglas**: [RN-23](05_reglas_de_negocio.md#rn-23), [RN-24](05_reglas_de_negocio.md#rn-24)

---

## Épica 10 — Liquidaciones y Honorarios

### F10.1 — Vista de liquidaciones
- **Dónde**: `liquidaciones.php`
- **Tabla**: Leg | Docente | Rol | Comisiones | Base | Plus | Total
- **Acciones**: Vista previa, Exportar Excel, Cerrar liquidación, Historial, ABM Salarios

### F10.2 — Cerrar liquidación
- **Efecto**: inmutabiliza la liquidación del período ([RN-22](05_reglas_de_negocio.md#rn-22))

### F10.3 — Historial de liquidaciones
- **Dónde**: botón "Historial" en `liquidaciones.php`

### F10.4 — ABM de salarios (grilla)
- **Dónde**: `salarios.php` → acceso restringido a super-admin (legajo 1 / impersonation)
- **Capacidad**: gestiona dos grillas:
  - **Base** por rol (PROFESOR/TUTOR/NEXO/COORDINADOR) con vigencia desde/hasta
  - **Plus** por (clave, rol, descripción) con vigencia
- **Reglas aplicadas**: [RN-31](05_reglas_de_negocio.md#rn-31), [RN-32](05_reglas_de_negocio.md#rn-32), [RN-33](05_reglas_de_negocio.md#rn-33)

### F10.5 — Gestión de Facturas (descubierto en segunda pasada)
- **Dónde**: `admin_facturas.php`
- **Quién**: super-admin
- **Funcionalidad**: ABM de facturas presentadas por docentes monotributistas
- **Tabla**: Fecha carga | Docente | Mes | Detalle | Archivo (PDF) | Tamaño | Estado | Pago | Acción
- **Filtros**: profesor, estado (pendiente/abonada), rango fechas, búsqueda libre
- **Acción**: cambiar estado de la factura (`pendiente` ↔ `abonada`)
- **Regla clave**: docentes que facturan NO se incluyen en la liquidación general — se pagan vía este flujo ([RN-35](05_reglas_de_negocio.md#rn-35))

### F10.6 — Separación contable factura/no-factura en liquidación (refinado)
- **Dónde**: `liquidaciones.php`
- **Funcionalidad**: la pantalla muestra 3 tablas:
  1. Detalle general (roles PROFESOR/TUTOR/COORDINADOR)
  2. NEXO (aparte pero suma al total) — [RN-36](05_reglas_de_negocio.md#rn-36)
  3. Docentes que facturan (no se incluyen en liquidación, se pagan por otro medio) — [RN-35](05_reglas_de_negocio.md#rn-35)
- **KPIs cabecera**: "Total sin Factura" + "Total con factura" — [RN-38](05_reglas_de_negocio.md#rn-38)
- **Filtros**: Cohorte + Mes + Legajo opcional — [RN-37](05_reglas_de_negocio.md#rn-37)

---

## Épica 11 — Perfil y Sesión

### F11.1 — Editar perfil
- **Dónde**: `perfil.php`
- **Campos editables**: nombre, dni, sexo, banco, cbu, alias_cbu, regional, email, factura, legajo_profesional
- **Campo solo lectura**: cuil_view

### F11.2 — Inbox de mensajes
- **Dónde**: `perfil.php`
- **Capacidad**: ver threads + responder
- **Regla**: [F3.4](#f34-mensajería-interna-inbox-del-docente)

### F11.3 — Logout
- **Dónde**: `logout.php`

---

## Épica 12 — Integración con Correct-IA (externa)

### F12.1 — Acceso a Correct-IA
- **Dónde**: link "Correct-IA" en menú Procesos → `https://olsoft.online/evalia/corrector/index.php`
- **Estado**: **fuera de alcance** de esta KB (módulo externo no recorrido)
