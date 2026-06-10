## ADDED Requirements

### Requirement: Crear encuentro único

El sistema SHALL permitir crear una `InstanciaEncuentro` sin slot padre (`slot_id=NULL`), proporcionando todos los campos requeridos: `materia_id`, `cohorte_id`, `fecha`, `hora_inicio`, `hora_fin`, `titulo`.

#### Scenario: Encuentro único exitoso

- **WHEN** se crea un encuentro único con todos los campos requeridos
- **THEN** el sistema retorna 201 con los datos de la instancia creada
- **AND** `slot_id` es `null`
- **AND** `estado` por defecto es `Programado`

#### Scenario: Encuentro único con meet_url opcional

- **WHEN** se crea un encuentro único con `meet_url="https://meet.google.com/abc-defg-hij"`
- **THEN** el sistema almacena la URL y la retorna en la respuesta

### Requirement: Listar instancias de encuentro

El sistema SHALL permitir listar instancias de encuentro con filtros opcionales: `materia_id`, `cohorte_id`, `estado` (Programado|Realizado|Cancelado), `fecha_desde`, `fecha_hasta`.

#### Scenario: Listar por materia y estado

- **WHEN** se solicita `GET /api/encuentros/instancias?materia_id=<uuid>&estado=Programado`
- **THEN** el sistema retorna solo instancias de esa materia con estado Programado

#### Scenario: Listar por rango de fechas

- **WHEN** se solicita `GET /api/encuentros/instancias?fecha_desde=2026-03-01&fecha_hasta=2026-03-31`
- **THEN** el sistema retorna solo instancias cuya fecha está dentro del rango (inclusive)

#### Scenario: Sin filtros

- **WHEN** se solicita `GET /api/encuentros/instancias` sin query params
- **THEN** el sistema retorna todas las instancias del tenant (limit 50, offset 0 por defecto)

### Requirement: Obtener instancia por ID

El sistema SHALL permitir obtener una instancia por su UUID.

#### Scenario: Obtener instancia existente

- **WHEN** se solicita `GET /api/encuentros/instancias/<instancia_id>`
- **THEN** el sistema retorna la instancia con todos sus campos

#### Scenario: Instancia no encontrada

- **WHEN** se solicita una instancia con UUID inexistente o soft-deleteada
- **THEN** el sistema retorna 404

### Requirement: Editar instancia de encuentro

El sistema SHALL permitir editar los campos `estado`, `meet_url`, `video_url` y `comentario` de una instancia. La fecha y hora PUEDEN modificarse si la instancia aún no pasó (fecha >= hoy).

#### Scenario: Cambiar estado a Realizado

- **WHEN** se modifica `estado` a `Realizado` vía `PATCH /api/encuentros/instancias/<instancia_id>`
- **THEN** el sistema actualiza el estado y retorna la instancia

#### Scenario: Agregar comentario

- **WHEN** se modifica `comentario` a "Se reprograma para la semana que viene"
- **THEN** el sistema actualiza el comentario y retorna la instancia

#### Scenario: Estado inválido

- **WHEN** se intenta cambiar `estado` a un valor no permitido (ej. "Pendiente")
- **THEN** el sistema retorna 422 con detalle de validación

#### Scenario: Editar fecha de instancia pasada

- **WHEN** se intenta modificar `fecha` de una instancia cuya fecha ya es anterior a hoy
- **THEN** el sistema retorna 422 indicando que no se puede modificar la fecha de un encuentro pasado

### Requirement: Generar fragmento HTML para aula virtual

El sistema SHALL generar un bloque HTML con el listado de encuentros de una materia y cohorte, formateado para incrustar en el aula virtual (Moodle).

#### Scenario: Generar HTML con encuentros

- **WHEN** se solicita `GET /api/encuentros/instancias/fragmento-lms?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** el sistema retorna HTML con clase `Content-Type: text/html`
- **AND** el HTML contiene una tabla/listado con fecha, hora y título de cada instancia no deleteada
- **AND** si hay `meet_url`, se incluye como link
- **AND** las instancias canceladas se marcan visualmente

#### Scenario: Sin encuentros

- **WHEN** no hay instancias para la materia y cohorte dadas
- **THEN** el sistema retorna HTML con un mensaje "Sin encuentros programados"

### Requirement: Soft-delete de instancia

El sistema SHALL permitir soft-deletear una instancia. Esto no afecta al slot padre ni a otras instancias.

#### Scenario: Soft-delete instancia

- **WHEN** se solicita `DELETE /api/encuentros/instancias/<instancia_id>`
- **THEN** la instancia se marca con `deleted_at = now()`
- **AND** el sistema retorna 204
