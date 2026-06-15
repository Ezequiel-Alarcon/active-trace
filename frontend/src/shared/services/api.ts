import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { tokenStore } from './tokenStore';

/**
 * Endpoints that should NOT receive a stale access token.
 * These are public auth endpoints that either issue a token or don't need one.
 */
const PUBLIC_AUTH_PATHS = [
  '/api/auth/login',
  '/api/auth/forgot',
  '/api/auth/reset',
];

/**
 * Single-flight refresh state.
 * At most one POST /api/auth/refresh is in-flight at any time.
 */
let refreshPromise: Promise<string> | null = null;

/**
 * Callback to invoke when a refresh fails (navigate to /login, clear session).
 * Set by AuthProvider via setLogoutCallback().
 */
let logoutCallback: (() => void) | null = null;

export function setLogoutCallback(fn: () => void): void {
  logoutCallback = fn;
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  withCredentials: true, // send refresh token cookie if backend uses httpOnly cookie
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request interceptor: attach access token ──────────────────────────────

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const url = config.url ?? '';
  const isPublicAuthPath = PUBLIC_AUTH_PATHS.some((path) => url.includes(path));

  if (!isPublicAuthPath) {
    const token = tokenStore.get();
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }
  }

  return config;
});

// ─── Response interceptor: transparent refresh + single-flight ─────────────

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean;
    };

    const status = error.response?.status;
    const url = originalRequest?.url ?? '';

    // 403 → permission error, surface immediately without refresh/retry
    if (status === 403) {
      return Promise.reject(error);
    }

    // 401 on the refresh endpoint itself → logout and reject
    if (status === 401 && url.includes('/api/auth/refresh')) {
      tokenStore.clear();
      refreshPromise = null;
      logoutCallback?.();
      return Promise.reject(error);
    }

    // 401 on auth step endpoints or the session endpoint → surface directly.
    // These endpoints use 401 semantically (not "token expired") so refresh is not appropriate.
    // /api/auth/session 401 means "no session" — TanStack Query catches it and isAuthenticated = false.
    // TODO: (REVIEW) NO_REFRESH_PATHS hardcodeado; mover a config si crece
    const NO_REFRESH_PATHS = [
      '/api/auth/login',
      '/api/auth/2fa/verify',
      '/api/auth/forgot',
      '/api/auth/reset',
      '/api/auth/session',
    ];
    if (status === 401 && NO_REFRESH_PATHS.some((p) => url.includes(p))) {
      return Promise.reject(error);
    }

    // 401 on any other endpoint → attempt transparent refresh (single-flight)
    if (status === 401 && !originalRequest._retried) {
      originalRequest._retried = true;

      if (!refreshPromise) {
        refreshPromise = apiClient
          .post<{ access_token: string }>('/api/auth/refresh')
          .then((res) => {
            const newToken = res.data.access_token;
            tokenStore.set(newToken);
            return newToken;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      try {
        const newToken = await refreshPromise;
        originalRequest.headers.set('Authorization', `Bearer ${newToken}`);
        return apiClient(originalRequest);
      } catch {
        // Refresh failed — already handled above (the refresh interceptor fires)
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);
