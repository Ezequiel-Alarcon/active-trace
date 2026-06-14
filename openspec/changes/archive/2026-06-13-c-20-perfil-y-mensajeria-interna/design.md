## Context

activia-trace currently has profile data in the `Usuario` model with PII fields encrypted at rest (C-07). Profile mutation is admin-only via `usuarios:gestionar`. There is no internal messaging between registered users — all outbound communication goes through the email-based system (C-12). F11.1, F3.4, F11.2, and FL-10 require self-service profile editing and an internal threaded inbox.

## Goals / Non-Goals

**Goals:**
- Authenticated users can GET their own profile with all non-sensitive fields visible and PII fields masked/decrypted per role.
- Authenticated users can PATCH editable fields (nombre, apellidos, banco, cbu/alias, regional, modalidad de cobro, legajo profesional). `cuil` is SOLO LECTURA.
- Internal threaded messaging between registered users: send, reply, inbox listing, thread read with read-receipt tracking.
- Multi-tenant isolation: all messages scoped to tenant via TenantScopedMixin.

**Non-Goals:**
- Notifications/push for new messages (no websockets, no email alerts for internal messages — out of scope).
- Attachments on messages.
- Group messaging (only 1:1).
- Deleting or editing sent messages.
- Bulk operations on inbox.

## Decisions

**D1 — Separate perfil router instead of reusing admin router.** The admin `usuarios` router requires `usuarios:gestionar`. The profile endpoint must work for any authenticated user with no permission check beyond authentication. A separate `routers/perfil.py` at `/api/perfil` follows the principle of least privilege and avoids permission confusion.

**D2 — `cuil` is SOLO LECTURA.** `cuil` is a fiscal identity key. Changing it has legal/compliance implications. The PATCH endpoint will validate that `cuil` is not in the request body (via a PerfilUpdate schema that omits the field entirely), and the GET endpoint returns it as read-only.

**D3 — PII re-encryption on profile update.** Fields `email`, `dni`, `cbu`, `alias_cbu` are stored encrypted (AES-256) in the Usuario model. The PerfilUpdate schema will support these fields, and the service layer will re-encrypt before passing to the repository, reusing existing encryption utilities from C-07.

**D4 — Threaded messages via `hilo_id`.** Messages are grouped into threads using `hilo_id`. When a new message is sent with no `hilo_id`, it starts a new thread (its own `id` becomes `hilo_id`). Replies carry the parent's `hilo_id`. This avoids a separate `Hilo` table while keeping thread grouping simple.

**D5 — `padre_id` for reply chains.** Each reply references the parent message, enabling the client to render nested conversations if needed. The reply endpoint validates that `padre_id` belongs to the same tenant and same `hilo_id`.

**D6 — `leido_at` as read receipt.** Initially NULL; set to `now()` when the recipient opens the thread via GET. Only the recipient's read marks count. No explicit "mark as read" endpoint — reading the thread implies marking.

**D7 — No special permission required.** Internal messages are a personal communication channel. Every authenticated user can send/receive. No `require_permission(...)` guard — only identity resolution from JWT (CurrentUser).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **Profile PII leak if encryption fails** | Encryption/decryption is already hardened in C-07; reuse same utilities; add explicit test for write-then-read round-trip |
| **Thread performance with deep chains** | Only 1:1 messaging; thread depth is bounded by user behaviour — no indexing concern at this scale; add composite index on `(tenant_id, hilo_id, created_at)` |
| **`leido_at` set on GET may not cover all reads** | Acceptable trade-off — no separate read-receipt endpoint; client-side marking would be unreliable |
