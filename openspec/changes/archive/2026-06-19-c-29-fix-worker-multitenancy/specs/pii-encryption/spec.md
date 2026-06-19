## MODIFIED Requirements

### Requirement: Comunicacion.destinatario SHALL be encrypted at rest

The `Comunicacion` model SHALL encrypt the `destinatario` field (recipient email/contact) using the existing AES-256-GCM helper from `core/security/crypto.py`. The encryption SHALL follow the same pattern as the `Usuario` model: store the encrypted value in `destinatario_enc` and a HMAC-SHA-256 in `destinatario_hash` for lookup. The plaintext `destinatario` column SHALL be retained only during the migration phase; the definitive fix removes it via a later migration (C-31). The AAD suffix SHALL be `"comunicacion.destinatario"`.

**The `set_destinatario()` method MUST NOT store the plaintext email in any column.** It SHALL only populate `destinatario_hash` and `destinatario_enc`. The plaintext `destinatario` column SHALL be removed from the table schema via a future migration.

#### Scenario: Creating a Comunicacion encrypts the destinatario

- **WHEN** a `Comunicacion` is created with `destinatario = "alumno@test.com"` in tenant `T1`
- **THEN** `Comunicacion.destinatario_enc` contains the AES-256-GCM ciphertext with AAD `"comunicacion.destinatario"`
- **AND** `Comunicacion.destinatario_hash` contains the HMAC-SHA-256 of `"alumno@test.com"`
- **AND** no column stores the plaintext `"alumno@test.com"` (after migration 025)

#### Scenario: Decryption of Comunicacion.destinatario_enc returns the original value

- **WHEN** a stored `Comunicacion`'s `destinatario_enc` is decrypted with `tenant_id=T1` and `aad_suffix="comunicacion.destinatario"`
- **THEN** the result is the original `destinatario` plaintext

#### Scenario: Cross-tenant decryption fails

- **WHEN** attempting to decrypt `destinatario_enc` from tenant `T1` with `tenant_id=T2` and the same AAD suffix
- **THEN** the helper raises `CryptoError` and no plaintext is returned

#### Scenario: Router calls set_destinatario instead of direct assignment

- **WHEN** `enqueue_mensajes` creates a `Comunicacion`
- **THEN** it calls `obj.set_destinatario(item.destinatario)` after object creation
- **AND** it does NOT assign `destinatario=item.destinatario` directly in the constructor

#### Scenario: set_destinatario does not store plaintext

- **WHEN** `set_destinatario("alumno@test.com")` is called on a `Comunicacion` instance
- **THEN** `self.destinatario` is NOT updated
- **AND** only `self.destinatario_hash` and `self.destinatario_enc` are populated
