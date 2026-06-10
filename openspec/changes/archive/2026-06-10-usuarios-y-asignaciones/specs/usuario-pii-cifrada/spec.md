# usuario-pii-cifrada Specification

## Purpose

Define el comportamiento de cifrado en reposo de los campos PII del modelo `Usuario` y el mecanismo de búsqueda determinística por email. Cada campo PII se cifra con AES-256-GCM usando `aad_suffix` único por campo. El email se busca por HMAC, no por ciphertext.

## ADDED Requirements

### Requirement: Usuario SHALL almacenar campos PII cifrados con AES-256-GCM

El sistema SHALL cifrar `email`, `dni`, `cuil`, `cbu` y `alias_cbu` al persistir un `Usuario` y SHALL descifrarlos al leerlos para uso interno. Cada campo usa un `aad_suffix` distinto (`usuario.email`, `usuario.dni`, `usuario.cuil`, `usuario.cbu`, `usuario.alias_cbu`) para que un ciphertext de un campo no sea descifrable como otro campo.

#### Scenario: Round-trip de cifrado para email

- **WHEN** se crea un Usuario con email="maria@garcia.com" en tenant A
- **AND** se persiste en base de datos
- **THEN** la columna `email_enc` contiene un ciphertext base64 distinto del plaintext
- **AND** al leer el Usuario, el servicio descifra `email_enc` y obtiene "maria@garcia.com"

#### Scenario: Ciphertext de email no es descifrable como dni

- **WHEN** se cifra "maria@garcia.com" con `aad_suffix="usuario.email"` para tenant A
- **AND** se intenta descifrar ese mismo ciphertext con `aad_suffix="usuario.dni"`
- **THEN** la operación falla con error de autenticación (tag mismatch)

#### Scenario: Ciphertext de un tenant no es descifrable en otro tenant

- **WHEN** se cifra "20123456" (DNI) con `tenant_id=A` y `aad_suffix="usuario.dni"`
- **AND** se intenta descifrar ese ciphertext con `tenant_id=B` y `aad_suffix="usuario.dni"`
- **THEN** la operación falla con error de autenticación (tag mismatch)

#### Scenario: Campos no-PII se almacenan en texto plano

- **WHEN** se persiste un Usuario con nombre="María", apellidos="García", legajo="L-1234"
- **THEN** las columnas `nombre`, `apellidos`, `legajo` contienen los valores en texto plano
- **AND** `nombre`, `apellidos` y `legajo` son legibles directamente desde la DB

### Requirement: Email lookup SHALL usar HMAC determinístico, no ciphertext

El sistema SHALL mantener una columna `email_hash` con el HMAC-SHA256 de `f"{tenant_id}:{email_lower}"` keyed por `ENCRYPTION_KEY`. La búsqueda de usuario por email SHALL filtrar por `(tenant_id, email_hash)`, nunca por `email_enc`.

#### Scenario: Búsqueda por email encuentra el usuario correcto

- **WHEN** existe un Usuario con email="maria@garcia.com" en tenant A
- **AND** se busca por email="maria@garcia.com" (lowercase) en tenant A
- **THEN** el repositorio encuentra el Usuario por `(tenant_id=A, email_hash=HMAC(A:maria@garcia.com))`

#### Scenario: Búsqueda por email no encuentra en otro tenant

- **WHEN** existe un Usuario con email="maria@garcia.com" en tenant A
- **AND** se busca por email="maria@garcia.com" en tenant B
- **THEN** el repositorio no encuentra resultados (hash distinto por tenant_id en el mensaje HMAC)

#### Scenario: Búsqueda por email es case-insensitive

- **WHEN** existe un Usuario con email="Maria@Garcia.com" en tenant A
- **AND** se busca por email="maria@garcia.com" en tenant A
- **THEN** el repositorio encuentra el Usuario (el hash se computa sobre el email lowercased)

### Requirement: Sistema SHALL garantizar unicidad de email por tenant vía índice único sobre email_hash

El sistema SHALL crear un índice único `(tenant_id, email_hash)` en la tabla `usuario`. Al intentar crear un segundo Usuario con el mismo email en el mismo tenant, la DB rechaza la inserción con violación de unique constraint.

#### Scenario: Email duplicado en el mismo tenant es rechazado

- **WHEN** existe un Usuario con email="maria@garcia.com" en tenant A
- **AND** se intenta crear otro Usuario con email="maria@garcia.com" en tenant A
- **THEN** el sistema retorna 409 Conflict con mensaje indicando email duplicado

#### Scenario: Email duplicado en distinto tenant es permitido

- **WHEN** existe un Usuario con email="maria@garcia.com" en tenant A
- **AND** se crea un Usuario con email="maria@garcia.com" en tenant B
- **THEN** el sistema crea el Usuario exitosamente (hashes distintos por tenant_id)

### Requirement: PII cifrada NUNCA debe aparecer en logs ni respuestas de error

El sistema SHALL garantizar que ningún campo PII descifrado (email, dni, cuil, cbu, alias_cbu) aparece en logs estructurados, mensajes de error HTTP, ni trazas de excepción. Los logs solo pueden contener `tenant_id`, `aad_suffix` y códigos de error opacos, nunca plaintext ni ciphertext.

#### Scenario: Error de unicidad de email no expone el email en texto plano

- **WHEN** se intenta crear un Usuario con email duplicado
- **AND** el sistema captura la excepción de unicidad
- **THEN** la respuesta HTTP contiene un mensaje genérico "Email duplicado" sin incluir la dirección de email
- **AND** los logs no contienen el email en texto plano
