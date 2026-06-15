/**
 * Types for the auth feature.
 * AuthErrorCode mirrors the `code` values returned by C-03 backend.
 */

export type AuthErrorCode =
  | 'AUTH_INVALID_CREDENTIALS'
  | 'AUTH_2FA_REQUIRED'
  | 'AUTH_2FA_INVALID'
  | 'AUTH_TOKEN_EXPIRED'
  | 'AUTH_TOKEN_REVOKED'
  | 'AUTH_RESET_EXPIRED'
  | 'AUTH_RESET_INVALID'
  | 'AUTH_ACCOUNT_LOCKED'
  | 'AUTH_TENANT_NOT_FOUND';

export interface SessionUser {
  user_id: string;
  email: string;
  tenant_id: string;
}

export interface Session {
  user: SessionUser;
  roles: string[];
  permissions: string[];
}

export interface LoginRequest {
  tenant_codigo: string;
  email: string;
  password: string;
  totp_code?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  totp_enabled?: boolean;
}

export interface AuthErrorResponse {
  code: AuthErrorCode;
  message: string;
}

export interface ForgotRequest {
  tenant_codigo: string;
  email: string;
}

export interface ResetRequest {
  token: string;
  new_password: string;
}
