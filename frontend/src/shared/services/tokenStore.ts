/**
 * In-memory singleton for storing JWT tokens (access + refresh).
 * Kept in memory (NOT localStorage) to reduce XSS attack surface.
 * On page reload both tokens are gone; the app re-authenticates via login.
 */
// TODO: (HACK) tokens en memoria se pierden al recargar la página; considerar sessionStorage cifrado si el UX lo requiere
let _token: string | null = null;
let _refreshToken: string | null = null;

export const tokenStore = {
  get(): string | null {
    return _token;
  },
  set(token: string): void {
    _token = token;
  },
  getRefresh(): string | null {
    return _refreshToken;
  },
  setRefresh(token: string): void {
    _refreshToken = token;
  },
  clear(): void {
    _token = null;
    _refreshToken = null;
  },
};
