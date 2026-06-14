# Proposal: C-20 — Perfil y Mensajería Interna

## Why

Users need to view and edit their own profile (nombre, apellidos, datos bancarios, datos fiscales, etc.) without requiring an admin — currently only `usuarios:gestionar` can do this. Separately, the platform lacks an internal inbox for threaded messages between registered users (profesores, coordinadores, tutores, etc.) that operates parallel to the existing email-based communication system (C-12). This covers F11.1, F3.4, F11.2, and FL-10.

## What Changes

- **`GET /api/perfil`**: Authenticated user reads their own profile (all non-PII fields plus masked PII).
- **`PATCH /api/perfil`**: Authenticated user edits editable fields of their own profile. `cuil` is SOLO LECTURA. Some fields may require re-encryption on write.
- **`MensajeInterno` model + migration `020_mensajes_internos`**: New table for internal threaded messages (TenantScopedMixin). Fields: `asunto`, `cuerpo`, `remitente_id` FK→Usuario, `destinatario_id` FK→Usuario, `hilo_id` UUID for grouping, `padre_id` FK→MensajeInterno (nullable), `leido_at` datetime (nullable).
- **Internal messaging API**:
  - `GET /api/mensajes/inbox` — list active threads for current user
  - `GET /api/mensajes/inbox/{hilo_id}` — read a thread's messages, marks as read
  - `POST /api/mensajes` — send a new message
  - `POST /api/mensajes/{mensaje_id}/reply` — reply within a thread
- **Logout (F11.3)**: No implementation — reuses existing `POST /api/auth/logout` from C-03.

## Capabilities

### New Capabilities
- `perfil-propio`: Own profile read/write (nombre, apellidos, datos fiscales, banco, cbu/alias, regional, modalidad de cobro, legajo profesional). `cuil` is SOLO LECTURA.
- `mensajeria-interna`: Internal threaded messaging between registered users, with inbox, thread read, send, and reply operations.

### Modified Capabilities
- (None — no existing spec-level behavior changes.)

## Impact

| Area | Impact |
|------|--------|
| **Models** | New `MensajeInterno` model (app/models/mensaje_interno.py) |
| **Migration** | `020_mensajes_internos.py` — create `mensaje_interno` table |
| **Schemas** | New `perfil.py` schemas (PerfilResponse, PerfilUpdate) + `mensajes.py` schemas |
| **Routers** | New `routers/perfil.py` (prefix `/api/perfil`) + `routers/mensajes.py` (prefix `/api/mensajes`) |
| **Services** | New `services/perfil.py` + `services/mensajes.py` |
| **Repositories** | New `repositories/mensajes.py` for MensajeInterno queries |
| **Main router** | Register both new routers in `main_router.py` |
| **Usuario model** | Reused as-is; PII fields (dni, cuil, cbu, alias_cbu) remain encrypted |
