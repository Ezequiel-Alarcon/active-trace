## 1. Migration — MensajeInterno table

- [x] 1.1 Create `backend/alembic/versions/020_mensajes_internos.py` with `mensaje_interno` table (TenantScopedMixin columns + `asunto`, `cuerpo`, `remitente_id`, `destinatario_id`, `hilo_id`, `padre_id`, `leido_at`) and indexes on `(tenant_id, remitente_id)`, `(tenant_id, destinatario_id)`, `(tenant_id, hilo_id)`
- [ ] 1.2 Run migration locally and verify rollback — blocked (production DB not reachable; schema verified via test model sync)

## 2. Model + Repository — MensajeInterno

- [x] 2.1 Create `backend/app/models/mensaje_interno.py` with `MensajeInterno` model (TenantScopedMixin, FK constraints to `usuario.id` for `remitente_id` and `destinatario_id`, self-referencing FK for `padre_id`)
- [x] 2.2 Create `backend/app/repositories/mensajes.py` with `MensajeInternoRepository` (list_inbox_threads, get_thread_messages, get_by_id, create, mark_as_read)

## 3. Schemas — Perfil

- [x] 3.1 Create `backend/app/schemas/perfil.py` with `PerfilResponse` (all Usuario fields: id, tenant_id, nombre, apellidos, email, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, fecha_nacimiento, genero, observaciones, created_at, updated_at) and `PerfilUpdate` (editable fields only — no cuil; all optional)

## 4. Schemas — Mensajería Interna

- [x] 4.1 Create `backend/app/schemas/mensajes.py` with `MensajeCreate` (asunto, cuerpo, destinatario_id, hilo_id optional), `MensajeReply` (asunto, cuerpo), `MensajeResponse` (all model fields), `InboxThreadItem` (hilo_id, remitente_id, destinatario_id, ultimo_asunto, ultimo_cuerpo, leido, ultima_actividad)

## 5. Service — Perfil

- [x] 5.1 Create `backend/app/services/perfil.py` with `PerfilService.get_profile(user_id)` that fetches Usuario and maps to PerfilResponse (decrypting PII)
- [x] 5.2 Add `PerfilService.update_profile(user_id, data: PerfilUpdate)` that re-encrypts PII fields and delegates to UsuarioRepository

## 6. Service — Mensajería Interna

- [x] 6.1 Create `backend/app/services/mensajes.py` with `MensajeService.send(data, remitente_id, tenant_id)` that validates destinatario_id exists in tenant, creates message, sets hilo_id = message.id when not provided
- [x] 6.2 Add `MensajeService.reply(parent_id, data, remitente_id, tenant_id)` that validates parent exists, copies hilo_id and swaps destinatario/remitente
- [x] 6.3 Add `MensajeService.list_inbox(user_id, tenant_id)` that returns thread summary via the repository
- [x] 6.4 Add `MensajeService.read_thread(hilo_id, user_id, tenant_id)` that returns thread messages and marks recipient's unread messages as read

## 7. Router — Perfil

- [x] 7.1 Create `backend/app/routers/perfil.py` with `GET /api/perfil` (no permission guard — just auth) and `PATCH /api/perfil` (validate no cuil, call service.update_profile)
- [x] 7.2 Register perfil_router in `main_router.py`

## 8. Router — Mensajería Interna

- [x] 8.1 Create `backend/app/routers/mensajes.py` with `POST /api/mensajes`, `POST /api/mensajes/{mensaje_id}/reply`, `GET /api/mensajes/inbox`, `GET /api/mensajes/inbox/{hilo_id}` — all with `Depends(get_current_user)` but no `require_permission`
- [x] 8.2 Register mensajes_router in `main_router.py`

## 9. Tests — Perfil

- [x] 9.1 Write tests for `PerfilService.get_profile` and `update_profile` (encryption round-trip, cuil exclusion, empty update)
- [x] 9.2 Write integration tests for `GET /api/perfil` and `PATCH /api/perfil` endpoints (auth, unauthorized, field-level validation)

## 10. Tests — Mensajería Interna

- [x] 10.1 Write tests for `MensajeService.send`, `reply`, `list_inbox`, `read_thread` (thread creation, reply chain, read receipt, cross-tenant isolation)
- [x] 10.2 Write integration tests for all four messaging endpoints
