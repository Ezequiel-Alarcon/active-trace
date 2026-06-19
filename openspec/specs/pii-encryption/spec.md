## ADDED Requirements

### Requirement: Comunicacion.destinatario SHALL be encrypted at rest

The `Comunicacion` model SHALL encrypt the `destinatario` field (recipient email/contact) using the existing AES-256-GCM helper from `core/security/crypto.py`. The encryption SHALL follow the same pattern as the `Usuario` model: store the encrypted value in `destinatario_enc` and a HMAC-SHA-256 in `destinatario_hash` for lookup. The plaintext `destinatario` column SHALL be retained only during the migration phase; the definitive fix removes it via a future migration (C-31). The AAD suffix SHALL be `"comunicacion.destinatario"`.

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

### Requirement: AES-256-GCM encryption helper is available for PII at rest

The system MUST provide a `core/security/crypto.py` module that exposes symmetric encryption and decryption functions using AES-256 in GCM mode. The helper MUST accept plaintext (string or bytes) plus a `tenant_id` and an optional `aad_suffix` and produce a self-contained ciphertext. The helper MUST also accept the same `tenant_id` and `aad_suffix` to decrypt and return the original plaintext. A round-trip on the same `(tenant_id, aad_suffix)` MUST yield the original plaintext byte-for-byte.

The system MUST refuse to start if `Settings.ENCRYPTION_KEY` is missing or is not exactly 32 bytes (256 bits). `ENCRYPTION_KEY` MUST be declared as a `SecretStr` in Pydantic settings so that it is not accidentally logged or serialized.

#### Scenario: Round-trip on the same tenant yields the original plaintext

- **WHEN** a value is encrypted with `tenant_id=A` and `aad_suffix="usuario.email"`
- **AND** the resulting ciphertext is then decrypted with `tenant_id=A` and `aad_suffix="usuario.email"`
- **THEN** the decrypted value equals the original plaintext exactly

#### Scenario: Decryption fails if the tenant is different

- **WHEN** a value is encrypted with `tenant_id=A`
- **AND** the resulting ciphertext is then decrypted with `tenant_id=B` (and the same `aad_suffix`)
- **THEN** the decryption raises an authentication-failure error and no plaintext is returned

#### Scenario: Decryption fails if the AAD suffix differs

- **WHEN** a value is encrypted with `aad_suffix="usuario.email"`
- **AND** the resulting ciphertext is then decrypted with `aad_suffix="usuario.cbu"` (and the same `tenant_id`)
- **THEN** the decryption raises an authentication-failure error and no plaintext is returned

#### Scenario: Decryption fails if the ciphertext is tampered with

- **WHEN** a single bit of the stored ciphertext is flipped
- **THEN** the decryption raises an authentication-failure error and no plaintext is returned

#### Scenario: Application refuses to start without a valid 32-byte key

- **WHEN** the application starts with `ENCRYPTION_KEY` unset, or shorter than 32 bytes, or longer than 32 bytes
- **THEN** the application fails fast with a configuration error and the FastAPI app does not begin accepting requests

### Requirement: The encryption helper never exposes plaintext in logs

The encryption helper MUST NOT log, print, or include in any exception message the plaintext, the decrypted value, or the ciphertext in a way that could leak PII. The only data the helper is allowed to log in production is the boolean outcome (`encrypted`, `decrypted`, `failed`), the `tenant_id` (which is already known and non-sensitive in the audit context), the `aad_suffix` (which is a column name, not data), and an opaque error code on failure.

#### Scenario: Encrypting a PII value does not leak the value into logs

- **WHEN** the helper encrypts the string `"12345678"` with `tenant_id=A` and `aad_suffix="usuario.dni"`
- **THEN** no log record produced during the operation contains the substring `"12345678"` or any base64 form of the ciphertext

#### Scenario: Decryption failure does not leak the plaintext

- **WHEN** the helper raises an authentication-failure error
- **THEN** the exception message and any log record produced do not contain the attempted plaintext, the ciphertext, or the expected AAD value

### Requirement: Each encryption uses a fresh random IV

The helper MUST generate a fresh 96-bit (12-byte) random IV for every encryption call. Two encryptions of the same plaintext with the same key and same `tenant_id`/`aad_suffix` MUST produce different ciphertexts (the IV is stored as a prefix of the ciphertext).

#### Scenario: Same plaintext encrypted twice yields different ciphertexts

- **WHEN** the same plaintext is encrypted twice in a row with the same `tenant_id` and `aad_suffix`
- **THEN** the two resulting ciphertexts are different byte sequences

### Requirement: The helper supports future key rotation through a `key_id`

The helper's signature MUST include a `key_id: int` parameter (default `1`). The `Settings` exposes a registry that maps `key_id` to a 32-byte key. In C-02 only `key_id=1` is configured; the registry is designed so that adding `key_id=2` in a future change does not require a function-signature change. The ciphertext MAY optionally include a `key_id` prefix; if it does, the helper MUST select the corresponding key from the registry on decrypt.

#### Scenario: Ciphertext records the `key_id` used to encrypt it

- **WHEN** a value is encrypted with `key_id=1`
- **THEN** the resulting ciphertext carries a `key_id` marker that allows the decrypt path to pick the correct key

- **WHEN** a value is encrypted with `key_id=1` and decrypted with the system configured to use `key_id=1`
- **THEN** decryption succeeds
