# frontend-encuentros-creation Specification

## Purpose

Formularios frontend para crear slots de encuentro recurrente (F6.1) y encuentros únicos (F6.2). Consume los endpoints del backend de C-13 (`POST /api/encuentros/slots`, `POST /api/encuentros/instancias/unico`). Extiende `EncuentrosPage` existente con tabs de creación.

## ADDED Requirements

### Requirement: SlotForm — Wizard de 4 pasos para crear slot recurrente

El sistema SHALL ofrecer un wizard de creación de slot de encuentro recurrente con 4 pasos: materia → día/hora → duración → preview/crear.

#### Scenario: Usuario completa wizard y crea slot exitosamente

- **WHEN** usuario selecciona materia, día de semana, hora inicio, hora fin, modalidad, link, fecha inicio, cantidad de semanas
- **AND** hace clic en "Siguiente" en cada paso
- **AND** en el paso 4 (preview) hace clic en "Crear slot"
- **THEN** el sistema envía `POST /api/encuentros/slots` con todos los datos
- **AND** tras respuesta 201, invalida la query `['slots']` de TanStack Query
- **AND** muestra mensaje de éxito y retorna a la lista de slots

#### Scenario: Validación de paso vacía impide avanzar

- **WHEN** usuario intenta avanzar al siguiente paso sin completar los campos requeridos del paso actual
- **THEN** el sistema muestra errores inline en los campos faltantes
- **AND** permanece en el paso actual

#### Scenario: Preview muestra las N instancias que se generarán

- **WHEN** usuario llega al paso 4 (preview)
- **THEN** el sistema muestra una tabla con las N fechas calculadas client-side (fecha_inicio + N semanas)
- **AND** la tabla incluye: fecha, hora inicio, hora fin, título

### Requirement: SlotForm — Selector de materia

El sistema SHALL incluir un selector de materia en el paso 1 del wizard.

#### Scenario: Usuario busca y selecciona materia

- **WHEN** usuario escribe en el campo de materia
- **THEN** el sistema muestra lista filtrada de materias del tenant
- **AND** al seleccionar, guarda `materia_id`

### Requirement: InstanciaUnicaForm — Formulario de encuentro único

El sistema SHALL ofrecer un formulario de creación de encuentro único con campos: materia, fecha, hora inicio, hora fin, modalidad, link, título.

#### Scenario: Usuario crea encuentro único exitosamente

- **WHEN** usuario completa todos los campos requeridos del formulario
- **AND** hace clic en "Crear"
- **THEN** el sistema envía `POST /api/encuentros/instancias/unico` con los datos
- **AND** tras respuesta 201, invalida la query `['encuentros']`
- **AND** muestra mensaje de éxito y resetea el formulario

#### Scenario: Fecha en pasado rechazada

- **WHEN** usuario ingresa una fecha anterior a hoy
- **THEN** el sistema muestra error de validación indicando que la fecha no puede ser pasada

### Requirement: Permiso de acceso a los formularios

El sistema SHALL verificar el permiso `encuentros:gestionar` antes de mostrar los tabs y formularios de creación.

#### Scenario: Usuario sin permiso no ve tabs de creación

- **WHEN** un usuario sin el permiso `encuentros:gestionar` accede a EncuentrosPage
- **THEN** los tabs "Crear slot" y "Crear único" no son visibles
- **AND** solo ve los tabs de visualización existentes (Encuentros, Slots, Guardias)

### Requirement: Hook useCreateSlot mutation

El sistema SHALL exponer un hook `useCreateSlot()` que ejecuta `POST /api/encuentros/slots` y retorna el resultado de la mutación.

#### Scenario: Mutación exitosa

- **WHEN** `useCreateSlot().mutateAsync(data)` se resuelve con 201
- **THEN** retorna los datos del slot creado

#### Scenario: Mutación falla con 422

- **WHEN** `useCreateSlot().mutateAsync(data)` recibe 422 (validación)
- **THEN** rechaza con el detalle de errores del backend

### Requirement: Hook useCreateInstanciaUnica mutation

El sistema SHALL exponer un hook `useCreateInstanciaUnica()` que ejecuta `POST /api/encuentros/instancias/unico` y retorna el resultado de la mutación.

#### Scenario: Mutación exitosa

- **WHEN** `useCreateInstanciaUnica().mutateAsync(data)` se resuelve con 201
- **THEN** retorna los datos de la instancia creada
