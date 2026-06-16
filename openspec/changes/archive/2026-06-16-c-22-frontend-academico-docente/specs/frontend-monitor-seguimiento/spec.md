## ADDED Requirements

### Requirement: Monitor de seguimiento de alumnos asignados (vista tutor/profesor)

El sistema SHALL proveer un monitor del estado de actividades de los alumnos asignados al usuario autenticado (TUTOR o PROFESOR). El alcance de los alumnos visibles MUST resolverse desde la sesión y el backend; ningún parámetro de la petición puede ampliar el alcance. La vista MUST consumir el endpoint correspondiente vía un hook de TanStack Query y mostrar un estado vacío cuando no hay alumnos que coincidan.

#### Scenario: El monitor muestra los alumnos asignados

- **WHEN** un TUTOR o PROFESOR abre el monitor de seguimiento
- **THEN** se renderiza el estado de actividades de los alumnos asignados a su sesión

#### Scenario: Estado vacío sin coincidencias

- **WHEN** ningún alumno asignado coincide con los filtros aplicados
- **THEN** la vista muestra un estado vacío informativo

### Requirement: Filtros del monitor de seguimiento

El sistema SHALL ofrecer filtros para acotar el monitor por alumno, correo, comisión, regional, actividad y mínimo de actividad cumplida. Los filtros MUST combinarse y aplicarse contra el backend, y MUST poder limpiarse para volver al estado sin filtrar.

#### Scenario: Filtrar por comisión y mínimo cumplido

- **WHEN** el usuario filtra por una comisión y un mínimo de actividad cumplida
- **THEN** la vista muestra solo los alumnos que cumplen ambos criterios

#### Scenario: Limpiar filtros restablece la vista

- **WHEN** el usuario pulsa limpiar filtros
- **THEN** la vista vuelve a mostrar todos los alumnos asignados sin filtrar
