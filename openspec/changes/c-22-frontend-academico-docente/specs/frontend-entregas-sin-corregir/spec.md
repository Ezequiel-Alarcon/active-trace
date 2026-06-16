## ADDED Requirements

### Requirement: Importación del reporte de finalización

El sistema SHALL permitir al PROFESOR subir el reporte de finalización de actividades del LMS para la comisión seleccionada. El upload MUST pasar por el cliente HTTP centralizado y consumir el endpoint de C-11. Mientras el cruce con las calificaciones está en curso la vista MUST mostrar un estado de carga.

#### Scenario: Subida del reporte de finalización

- **WHEN** el PROFESOR sube un reporte de finalización válido para su comisión
- **THEN** el backend cruza el reporte con las calificaciones y devuelve las posibles entregas sin corregir

### Requirement: Tabla de posibles entregas sin corregir

El sistema SHALL mostrar la tabla de posibles entregas sin corregir resultante del cruce, identificadas por alumno y actividad. Cuando el cruce no produce resultados la vista MUST mostrar un estado vacío informativo.

#### Scenario: Tabla con entregas detectadas

- **WHEN** el cruce detecta entregas potencialmente sin corregir
- **THEN** la tabla muestra cada entrada identificada por alumno y actividad

#### Scenario: Estado vacío sin entregas detectadas

- **WHEN** el cruce no detecta ninguna entrega sin corregir
- **THEN** la vista muestra un estado vacío informativo

### Requirement: Export del listado de entregas sin corregir

El sistema SHALL ofrecer una acción para exportar el listado de entregas sin corregir como archivo descargable. La acción MUST estar deshabilitada cuando no hay entregas detectadas.

#### Scenario: Export con datos

- **WHEN** hay entregas sin corregir detectadas y el PROFESOR pulsa exportar
- **THEN** se descarga un archivo con el listado de entregas

#### Scenario: Export deshabilitado sin datos

- **WHEN** no hay entregas sin corregir detectadas
- **THEN** la acción de exportar está deshabilitada
