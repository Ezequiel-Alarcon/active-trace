## ADDED Requirements

### Requirement: Upload del export de calificaciones con preview

El sistema SHALL permitir al PROFESOR subir el archivo de calificaciones exportado del LMS para la comisión seleccionada y MUST presentar una vista previa con las actividades y los alumnos detectados por el backend antes de confirmar nada. El upload MUST pasar por el cliente HTTP centralizado (`@/shared/services/api`) y consumir el endpoint de importación de C-10. Mientras el procesamiento está en curso, la vista MUST mostrar un estado de carga; ante un error de procesamiento MUST mostrar el mensaje del backend sin perder el archivo elegido.

#### Scenario: Preview de actividades y alumnos tras subir el archivo

- **WHEN** el PROFESOR sube un archivo de calificaciones válido para su comisión
- **THEN** el backend procesa el archivo y la vista muestra la lista de actividades detectadas y los alumnos detectados
- **AND** todavía no se ejecuta ningún cómputo de análisis

#### Scenario: Error de procesamiento se reporta al usuario

- **WHEN** el backend rechaza el archivo subido (formato inválido o sin columnas reconocibles)
- **THEN** la vista muestra el mensaje de error devuelto por el backend
- **AND** no se genera ningún preview de actividades

### Requirement: Selección de actividades a incluir en el análisis

El sistema SHALL permitir que el PROFESOR seleccione, desde el preview, qué actividades incluir en el análisis. La selección MUST poder marcar/desmarcar actividades individualmente y MUST enviarse al backend al confirmar la configuración. Si no hay ninguna actividad seleccionada, la confirmación MUST quedar deshabilitada.

#### Scenario: El profesor incluye un subconjunto de actividades

- **WHEN** el PROFESOR marca un subconjunto de las actividades detectadas y confirma
- **THEN** la configuración enviada al backend incluye exactamente las actividades seleccionadas

#### Scenario: Sin actividades seleccionadas no se puede confirmar

- **WHEN** el PROFESOR no tiene ninguna actividad marcada
- **THEN** la acción de confirmar queda deshabilitada

### Requirement: Configuración del umbral de aprobación

El sistema SHALL permitir configurar el umbral de aprobación en porcentaje, con valor por defecto 60%. El valor MUST validarse en el rango 0–100 mediante el esquema de formulario (Zod) antes de enviarse. Al confirmar, el umbral y la selección de actividades MUST persistirse vía el endpoint de C-10 y los cómputos de análisis MUST recalcularse con ese umbral.

#### Scenario: Umbral por defecto

- **WHEN** el PROFESOR llega a la configuración de umbral sin haberlo modificado
- **THEN** el campo muestra 60% como valor inicial

#### Scenario: Umbral fuera de rango es rechazado por validación

- **WHEN** el PROFESOR ingresa un umbral de 150
- **THEN** el formulario muestra un error de validación
- **AND** la confirmación no se envía al backend

#### Scenario: Confirmar persiste umbral y recalcula

- **WHEN** el PROFESOR fija un umbral válido y confirma con al menos una actividad seleccionada
- **THEN** el umbral y las actividades se envían al backend
- **AND** las vistas de análisis reflejan el nuevo cómputo
