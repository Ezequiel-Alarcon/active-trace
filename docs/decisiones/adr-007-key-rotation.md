# ADR-007 — Seam de rotación de claves para cifrado en reposo

- **Estado**: Aceptada
- **Fecha**: 2026-06-09
- **Contexto**: C-02 (core-models-y-tenancy)
- **Reemplaza**: —

## Contexto

Ciframos PII (email, DNI, CUIL, CBU, alias_cbu) en reposo con AES-256-GCM
(`backend/app/core/security/crypto.py`). La política de seguridad exige
que la clave de cifrado sea rotable sin downtime y sin pérdida de datos.

## Decisión

- El helper `encrypt()`/`decrypt()`/`encrypt_bytes()`/`decrypt_bytes()`
  acepta un parámetro `key_id: int = 1` desde el día 0, aunque la versión
  C-02 de `Settings` solo cargue la clave `1`.
- El blob cifrado lleva un header `version(1) || key_id(1) || nonce(12) ||
  tag(16) || ciphertext`. El `key_id` permite que un cambio futuro cargue
  varias claves en `Settings.key_registry()` y que `decrypt` elija la
  correcta leyendo el header.
- `Settings.key_registry()` está implementado como método (no atributo)
  para que un cambio futuro a un secret manager (Vault, AWS KMS, etc.)
  reemplace la implementación sin tocar la firma.

## Consecuencias

- **Positivas**: rotar claves no requiere un cambio de formato de blob.
  Re-cifrar columnas existentes es un job batch que puede correr offline.
- **Trade-offs conocidos**: la rotación retroactiva (re-cifrar ciphertexts
  con la nueva clave) es un proyecto aparte que **no** se implementa en
  C-02. Queda documentado en `docs/ARQUITECTURA.md` §10 (R2: "soft delete
  puede acumular basura") y §5 (PII cifrada).
- **Futuro**: cuando aparezca el primer trigger de rotación (compromiso de
  clave, política regulatoria, etc.), se agrega `key_id=2` al registry, se
  re-cifra por批次, y se actualiza `CURRENT_KEY_ID`.

## Alternativas consideradas

- **Fernet (cryptography)**: simple pero no permite AAD arbitrario. La
  atadura a `tenant_id` (D4 del design de C-02) se pierde.
- **Envelope encryption con KMS**: correcto, fuera de presupuesto MVP.
  Roadmap Fase 2+.
- **Sin `key_id` en el blob**: rechazo. Agregarlo retroactivamente obliga
  a re-cifrar TODOS los ciphertexts. Mejor incluirlo desde el día 0.
