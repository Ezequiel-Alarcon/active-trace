## ADDED Requirements

### Requirement: Comunicacion.destinatario SHALL be encrypted at rest

The `Comunicacion` model SHALL encrypt the `destinatario` field (recipient email/contact) using the existing AES-256-GCM helper from `core/security/crypto.py`. The encryption SHALL follow the exact pattern used by the `Usuario` model: store the encrypted value in `email_enc` (bytes) and a SHA-256 HMAC in `email_hash` for lookup. The plaintext `destinatario` column SHALL be replaced by these two columns.

The AAD suffix SHALL be `"comunicacion.destinatario"`.

#### Scenario: Creating a Comunicacion encrypts the destinatario

- **WHEN** a `Comunicacion` is created with `destinatario = "alumno@test.com"` in tenant `T1`
- **THEN** `Comunicacion.email_enc` contains the AES-256-GCM ciphertext with AAD `"comunicacion.destinatario"`
- **AND** `Comunicacion.email_hash` contains the SHA-256 HMAC of `"alumno@test.com"`
- **AND** the plaintext `destinatario` is never stored

#### Scenario: Decryption of Comunicacion.email_enc returns the original value

- **WHEN** a stored `Comunicacion`'s `email_enc` is decrypted with `tenant_id=T1` and `aad_suffix="comunicacion.destinatario"`
- **THEN** the result is the original `destinatario` plaintext

#### Scenario: Cross-tenant decryption fails

- **WHEN** attempting to decrypt `email_enc` from tenant `T1` with `tenant_id=T2` and the same AAD suffix
- **THEN** the helper raises `CryptoError` and no plaintext is returned
