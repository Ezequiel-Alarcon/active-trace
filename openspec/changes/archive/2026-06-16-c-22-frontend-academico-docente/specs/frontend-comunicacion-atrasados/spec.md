## ADDED Requirements

### Requirement: Selección de alumnos atrasados para comunicar

El sistema SHALL permitir, desde la vista de atrasados, seleccionar uno o más alumnos como destinatarios de la comunicación. La acción de previsualizar/enviar MUST quedar deshabilitada cuando no hay ningún destinatario seleccionado. La feature MUST exigir el permiso `comunicacion:enviar` en la sesión.

#### Scenario: Selección de uno o más destinatarios

- **WHEN** el PROFESOR marca uno o más alumnos atrasados
- **THEN** la acción de previsualizar la comunicación queda habilitada

#### Scenario: Sin destinatarios la acción queda deshabilitada

- **WHEN** no hay ningún alumno atrasado seleccionado
- **THEN** la acción de previsualizar/enviar está deshabilitada

### Requirement: Preview de la comunicación por alumno

El sistema SHALL presentar una previsualización del asunto y cuerpo del mensaje, personalizada por cada alumno seleccionado, antes de cualquier envío. El envío MUST requerir una confirmación explícita posterior al preview.

#### Scenario: Preview antes de enviar

- **WHEN** el PROFESOR previsualiza la comunicación para los destinatarios seleccionados
- **THEN** se muestra el asunto y cuerpo personalizado por cada alumno
- **AND** ningún mensaje se encola hasta que el PROFESOR confirma el envío

### Requirement: Envío a la cola de comunicaciones

El sistema SHALL encolar los mensajes confirmados vía el endpoint de C-12, dejando cada mensaje en estado inicial Pendiente. El envío MUST pasar por el cliente HTTP centralizado. Tras un envío exitoso la vista MUST reflejar que los mensajes ingresaron a la cola.

#### Scenario: Confirmar encola los mensajes

- **WHEN** el PROFESOR confirma el envío tras el preview
- **THEN** los mensajes se encolan en estado Pendiente vía el endpoint de C-12
- **AND** la vista pasa a mostrar el seguimiento de estados

### Requirement: Tracking de estados en tiempo real

El sistema SHALL mostrar el estado de cada mensaje encolado y MUST actualizarlo en tiempo real mediante polling hasta que cada mensaje alcanza un estado terminal (OK, Fallido o Cancelado). Los estados visibles MUST cubrir la transición Pendiente → En envío → OK / Fallido / Cancelado. El polling MUST detenerse cuando todos los mensajes del lote están en estado terminal.

#### Scenario: El estado avanza de Pendiente a terminal

- **WHEN** un mensaje encolado pasa de Pendiente a En envío y luego a OK en el backend
- **THEN** la vista refleja cada transición de estado vía polling
- **AND** el indicador del mensaje queda en OK al alcanzar el estado terminal

#### Scenario: El polling se detiene en estados terminales

- **WHEN** todos los mensajes del lote alcanzaron un estado terminal (OK, Fallido o Cancelado)
- **THEN** el polling de estados se detiene
