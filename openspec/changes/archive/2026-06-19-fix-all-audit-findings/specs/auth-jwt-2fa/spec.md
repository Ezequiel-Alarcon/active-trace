## MODIFIED Requirements

### Requirement: Refresh token rotation SHALL generate a NEW token and detect reuse

**Change**: The current implementation re-signs the same refresh token on rotation. This MUST be fixed to:
1. Generate a completely new JWT refresh token on each rotation (new `jti`, new UUID)
2. Store the new token's Argon2id hash in a new `auth_session` row
3. Invalidate the old session row by setting `revoked_at`
4. Link old and new sessions via `rotated_to_id` / `replaced_by_id`
5. If a previously revoked token is presented, revoke ALL session rows reachable via the rotation chain (reuse detection)

(The existing spec already describes this correctly in its `### Requirement: Refresh token rotation revokes the old session...` block. The implementation did not match the spec. This delta confirms the spec is correct and must be properly implemented.)

#### Scenario: A valid refresh token rotates to a new session with a new jti

- **WHEN** `POST /api/auth/refresh` is called with a valid, non-revoked refresh token
- **THEN** a new `auth_session` row is created with a new `jti`, new `refresh_token_hash`, new UUID, and `expires_at = now() + REFRESH_TOKEN_EXPIRE_MINUTES`
- **AND** the old session row has `revoked_at = now()`
- **AND** `old_session.rotated_to_id` points to the new session's id
- **AND** `new_session.replaced_by_id` points to the old session's id
- **AND** the response contains a NEW refresh token (different from the previous one)

#### Scenario: Reusing a rotated token triggers chain-wide revocation

- **WHEN** `POST /api/auth/refresh` is called with a refresh token whose session row has `revoked_at IS NOT NULL`
- **THEN** every session in the rotation chain (follow `rotated_to_id` forward) has `revoked_at = now()` set
- **AND** the response is `401` with `code = "AUTH_TOKEN_REVOKED"`
- **AND** an audit event with action `AUTH_REFRESH_REUSE_DETECTED` is emitted
