## ADDED Requirements

### Requirement: Crear slot de encuentro recurrente

El sistema SHALL permitir crear un `SlotEncuentro` con `cant_semanas` (mínimo 1, máximo 52). Al crearlo, el sistema MUST generar automáticamente `cant_semanas` instancias de `InstanciaEncuentro`, una por semana a partir de `fecha_inicio`. Cada instancia generada hereda los datos del slot (materia_id, cohorte_id, titulo, hora_inicio, hora_fin, meet_url, video_url) y referencia al slot vía `slot_id`.

#### Scenario: Slot recurrente con cant_semanas=4

- **WHEN** se crea un SlotEncuentro con `cant_semanas=4` y `fecha_inicio=2026-03-02` (lunes)
- **THEN** el sistema genera 4 instancias con fechas: 2026-03-02, 2026-03-09, 2026-03-16, 2026-03-23
- **AND** cada instancia tiene `slot_id` apuntando al slot creado
- **AND** el sistema retorna 201 con los datos del slot

#### Scenario: cant_semanas excede el máximo

- **WHEN** se intenta crear un SlotEncuentro con `cant_semanas=53`
- **THEN** el sistema retorna 422 con detalle de validación

#### Scenario: cant_semanas es 0 o negativo

- **WHEN** se intenta crear un SlotEncuentro con `cant_semanas=0`
- **THEN** el sistema retorna 422 con detalle de validación

### Requirement: Listar slots de encuentro

El sistema SHALL permitir listar los slots de encuentro del tenant, filtrados opcionalmente por `materia_id`, `cohorte_id` o ambos.

#### Scenario: Listar slots por materia y cohorte

- **WHEN** se solicita `GET /api/encuentros/slots?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** el sistema retorna solo los slots que coinciden con ambos filtros
- **AND** no retorna slots soft-deleteados

### Requirement: Obtener slot por ID

El sistema SHALL permitir obtener un slot por su UUID, incluyendo sus datos y la lista de instancias asociadas.

#### Scenario: Obtener slot con instancias

- **WHEN** se solicita `GET /api/encuentros/slots/<slot_id>`
- **THEN** el sistema retorna el slot con todos sus campos
- **AND** incluye la lista de instancias asociadas (solo las no deleteadas)

#### Scenario: Slot no encontrado

- **WHEN** se solicita un slot con UUID inexistente o soft-deleteado
- **THEN** el sistema retorna 404

### Requirement: Editar slot de encuentro

El sistema SHALL permitir editar los campos `titulo`, `dia_semana`, `hora_inicio`, `hora_fin`, `meet_url`, `video_url` de un slot existente. La edición del slot NO modifica las instancias ya generadas.

#### Scenario: Editar meet_url del slot

- **WHEN** se modifica `meet_url` de un slot existente vía `PATCH /api/encuentros/slots/<slot_id>`
- **THEN** el sistema actualiza solo los campos enviados
- **AND** las instancias ya generadas mantienen sus valores originales

### Requirement: Soft-delete de slot de encuentro

El sistema SHALL permitir soft-deletear un slot. Las instancias asociadas se preservan con sus datos históricos.

#### Scenario: Soft-delete slot

- **WHEN** se solicita `DELETE /api/encuentros/slots/<slot_id>`
- **THEN** el slot se marca con `deleted_at = now()`
- **AND** las instancias asociadas no se modifican
- **AND** el sistema retorna 204
