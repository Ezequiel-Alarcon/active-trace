import { apiClient } from '@/shared/services/api';
import { tokenStore } from '@/shared/services/tokenStore';
import type {
  LoginRequest,
  LoginResponse,
  ForgotRequest,
  ResetRequest,
  AuthErrorResponse,
} from '../types/session';
import type { AxiosError } from 'axios';

/**
 * Extract the auth error code from an Axios error response.
 * Returns null if the shape doesn't match the expected error format.
 */
export function extractAuthErrorCode(err: unknown): string | null {
  const axiosErr = err as AxiosError<AuthErrorResponse>;
  return axiosErr?.response?.data?.code ?? null;
}

/**
 * POST /api/auth/login
 */
export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/api/auth/login', payload);
  return response.data;
}

/**
 * POST /api/auth/2fa/verify
 */
export async function verify2fa(payload: {
  tenant_codigo: string;
  email: string;
  password: string;
  totp_code: string;
}): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/api/auth/2fa/verify', payload);
  return response.data;
}

/**
 * POST /api/auth/forgot
 * Always returns a neutral message (no account enumeration).
 */
export async function forgotPassword(payload: ForgotRequest): Promise<void> {
  await apiClient.post('/api/auth/forgot', payload);
}

/**
 * POST /api/auth/reset
 */
export async function resetPassword(payload: ResetRequest): Promise<void> {
  await apiClient.post('/api/auth/reset', payload);
}

/**
 * POST /api/auth/logout
 * Sends the in-memory refresh token so the backend can revoke it.
 * If no refresh token is present (already cleared), the call is skipped —
 * the caller (useLogout) always clears the local session regardless.
 */
export async function logout(): Promise<void> {
  const refreshToken = tokenStore.getRefresh();
  if (!refreshToken) return;
  await apiClient.post('/api/auth/logout', { refresh_token: refreshToken });
}
