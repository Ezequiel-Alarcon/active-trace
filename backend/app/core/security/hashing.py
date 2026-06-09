"""Deterministic search hashes for fields that are also stored encrypted.

AES-256-GCM with a random nonce is correct for confidentiality but not for
equality lookup (each encryption of the same plaintext yields a different
ciphertext). The standard pattern is to keep the encrypted field for
confidentiality (`email_enc`) and store a separate **deterministic** HMAC
for lookup (`email_hash`). The HMAC key is the same `ENCRYPTION_KEY`
already protected by the deployment; compromising it is a total compromise
of the auth subsystem, not an additional surface.

AAD for the HMAC is the tenant id, so the same email in two tenants
produces two different hashes (cross-tenant search is impossible).
"""

from __future__ import annotations

import hashlib
import hmac

from app.core.config import get_settings


def hash_email_for_search(email_lower: str, tenant_id) -> str:
    """Return a hex SHA-256 HMAC of `f"{tenant_id}:{email_lower}"` keyed
    by the deployment's `ENCRYPTION_KEY`. Deterministic, indexed, 64 chars.

    `email_lower` is the already-lowercased email. `tenant_id` may be a
    `UUID` or any object that stringifies uniquely.
    """
    settings = get_settings()
    key = settings.key_registry()[settings.current_key_id()]
    msg = f"{tenant_id}:{email_lower}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()
