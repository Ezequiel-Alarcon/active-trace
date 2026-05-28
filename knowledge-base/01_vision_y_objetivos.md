# 01 — Visión y Objetivos

## Propósito del sistema

PulseUPs® es una **plataforma de gestión académica y rendimiento estudiantil** construida como capa de orquestación encima de Moodle. Resuelve el problema de que Moodle por sí solo no permite:

- Consolidar calificaciones de múltiples actividades en una vista accionable.
- Detectar y comunicar atrasos a alumnos de forma masiva y personalizada.
- Coordinar a equipos docentes (asignaciones, vigencias, jerarquías) a través de comisiones.
- Operar liquidaciones de honorarios contra la actividad efectiva del docente.

El subtítulo institucional lo confirma: **"Gestor de Rendimiento Académico & Recordatorios"**.

## Objetivos por actor

### Para el PROFESOR (rol observado: "Cortez Alberto")
- Importar Excel de calificaciones exportado de Moodle por materia.
- Detectar alumnos atrasados (sin entrega o con nota < umbral configurable, default 60%).
- Detectar trabajos prácticos entregados pero **sin corregir** por el docente.
- Enviar recordatorios personalizados por email a alumnos (con previsualización).
- Registrar encuentros sincrónicos (slots semanales + instancias).
- Llevar registro de guardias realizadas.
- Recibir y responder mensajes internos en su perfil.
- Gestionar tareas asignadas por la coordinación.

### Para el COORDINADOR / ADMINISTRADOR ACADÉMICO
- Gestionar el padrón completo de docentes (alta, datos bancarios, estado).
- Asignar docentes a materias × carrera × cohorte × comisión, en bulk o individualmente.
- Definir la estructura académica (carreras, cohortes, programas, fechas de parciales).
- Operar el monitor general de actividades para detectar alumnos en riesgo a nivel institucional.
- Publicar avisos con scope (materia/cohorte) y severity.
- Auditar las acciones de cada docente (panel `admin.php`).
- Clonar equipos docentes entre cohortes para acelerar el setup de inicio de cuatrimestre.

### Para el ADMIN FINANCIERO (rol inferido — acceso restringido)
- Calcular y cerrar liquidaciones por docente con base + plus.
- Mantener la grilla de salarios (`salarios.php` → "No autorizado" para rol PROFESOR).
- Aprobar envíos masivos de mail (`admin_mail_approval.php` → redirect para rol PROFESOR).

### Para el ALUMNO
- **No se observó UI propia para alumno**. El alumno es **objeto** de la herramienta (sujeto observado, destinatario de mails), no usuario directo. Toda interacción del alumno parece ocurrir en Moodle.

## Alcance funcional (lo que SÍ hace)

1. **Ingesta de datos desde Moodle**: Excel de calificaciones + CSV/Excel de finalización + padrón de participantes.
2. **Consolidación y análisis**: rankings, atrasados, TPs sin corregir, notas finales agrupadas.
3. **Comunicación saliente**: mails personalizados por alumno con preview HTML antes del envío.
4. **Gestión de equipos docentes**: ABM, asignaciones masivas, vigencias por contrato.
5. **Calendario académico**: fechas de parciales/TP/coloquios + encuentros recurrentes.
6. **Avisos del sistema**: tablón con segmentación por rol/scope/cohorte.
7. **Coloquios**: convocatorias, reservas con cupos, registro académico consolidado.
8. **Liquidaciones**: cálculo base + plus por docente, exportación a Excel.
9. **Tareas internas**: workflow profesor ↔ coordinación con comentarios y estados.
10. **Auditoría**: log de acciones con IP/UserAgent + métricas de uso por docente.

## Fuera de alcance (lo que NO hace, según se observa)

- **No es un LMS**: no aloja material didáctico ni recibe entregas — eso vive en Moodle.
- **No tiene UI para el alumno**: el alumno no se loguea acá.
- **No corrige automáticamente**: Correct-IA es un módulo externo (`/evalia/corrector/`).
- **No gestiona inscripciones**: las comisiones y matrículas vienen importadas desde Moodle.
- **No emite certificados ni títulos**: registro académico es solo consolidación de notas.

## Métrica observada del uso real

Del Panel (`admin.php`) se infiere actividad sostenida:
- Un docente registrado tiene **278 emails OK** y **221 cancelados** en una sola materia.
- El log de acciones está acotado a "máx. 200" recientes — indica volumen alto.
- La tabla de guardias tiene **250 registros** activos en el momento del análisis.
- La tabla de tareas admin tiene **443 registros**.

El sistema está claramente **en producción activa**.
