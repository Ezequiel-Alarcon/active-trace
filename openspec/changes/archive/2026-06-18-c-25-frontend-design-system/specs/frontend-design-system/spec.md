## ADDED Requirements

### Requirement: Paleta de tokens visuales y colores semánticos de estado

El sistema SHALL exponer una paleta centralizada de tokens visuales (color, espaciado, tipografía) y un mapa de colores semánticos de estado, de modo que ninguna página defina colores de estado ad-hoc. Los colores semánticos SHALL ser: `atrasado`/`fallido` → rojo, `aprobado`/`enviado` → verde, `pendiente`/`cancelado` → ámbar, `en-envio`/acento primario → azul, `neutro`/`pendiente-cola` → gris.

#### Scenario: Un estado semántico resuelve a un color consistente

- **WHEN** un componente solicita el color del estado `aprobado`
- **THEN** el sistema SHALL devolver el mismo conjunto de clases (verde) que devuelve para `aprobado` en cualquier otra vista

#### Scenario: La paleta vive en una única fuente

- **WHEN** se necesita cambiar el color del acento primario
- **THEN** SHALL bastar editar la definición de tokens (un único lugar) sin tocar las páginas

### Requirement: Componente Button reutilizable

El sistema SHALL proveer un componente `Button` con variantes `primary` (azul `blue-600`), `secondary` (gris) y `danger` (rojo), que soporte estado `disabled` y que sea PascalCase, sin `any`, menor a 200 LOC y sin estilos inline.

#### Scenario: Variante primaria

- **WHEN** se renderiza `<Button variant="primary">Guardar</Button>`
- **THEN** el botón SHALL mostrarse con fondo azul `blue-600` y texto blanco

#### Scenario: Estado deshabilitado

- **WHEN** se renderiza `<Button disabled>`
- **THEN** el botón SHALL aparecer atenuado (opacidad reducida) y SHALL ignorar clics

### Requirement: Componente Badge y StatusBadge

El sistema SHALL proveer un `Badge` genérico y un `StatusBadge` que reciba un estado semántico y aplique el color correspondiente del mapa de colores semánticos, sin que el consumidor escriba clases de color.

#### Scenario: StatusBadge de atraso

- **WHEN** se renderiza `<StatusBadge estado="atrasado">Atrasado</StatusBadge>`
- **THEN** el badge SHALL mostrarse con fondo rojo claro y texto rojo

#### Scenario: StatusBadge de estado de cola

- **WHEN** se renderiza `<StatusBadge estado="en-envio" />`
- **THEN** el badge SHALL mostrarse con el color azul definido para estados de cola en envío

### Requirement: Componente DataTable accesible

El sistema SHALL proveer un `DataTable` que reciba columnas y filas tipadas (genérico, sin `any`), renderice un `<table>` semántico con encabezados, soporte selección por checkbox opcional y muestre un estado vacío cuando no hay filas.

#### Scenario: Tabla con datos

- **WHEN** se pasa un arreglo de filas no vacío
- **THEN** el `DataTable` SHALL renderizar un `<thead>` con los encabezados y una fila por elemento

#### Scenario: Tabla vacía

- **WHEN** se pasa un arreglo de filas vacío
- **THEN** el `DataTable` SHALL renderizar el componente `EmptyState` en lugar del cuerpo de la tabla

### Requirement: Componentes de layout de página (PageHeader, Card, KpiCard, FilterBar, EmptyState)

El sistema SHALL proveer componentes de composición de página: `PageHeader` (título + acciones), `Card` (contenedor con borde y padding), `KpiCard` (métrica con número grande y etiqueta), `FilterBar` (contenedor de filtros horizontal) y `EmptyState` (mensaje informativo gris). Cada uno SHALL ser PascalCase, menor a 200 LOC, sin `any` y sin estilos inline.

#### Scenario: KpiCard muestra una métrica

- **WHEN** se renderiza `<KpiCard label="Atrasados" value={12} />`
- **THEN** SHALL mostrar el número `12` destacado y la etiqueta `Atrasados`

#### Scenario: EmptyState informativo

- **WHEN** se renderiza `<EmptyState>No hay datos importados.</EmptyState>`
- **THEN** SHALL mostrar el mensaje dentro de un contenedor gris con `role="status"`

### Requirement: Barrel export y ausencia de estilos inline

El sistema SHALL exponer todos los componentes de la capa UI desde un único punto de importación (`@/shared/ui`) y NO SHALL usar estilos inline (atributo `style`) salvo para valores dinámicos no expresables en Tailwind.

#### Scenario: Importación centralizada

- **WHEN** una página necesita `Button` y `StatusBadge`
- **THEN** SHALL poder importarlos desde `@/shared/ui` en una sola sentencia
