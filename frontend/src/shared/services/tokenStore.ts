/**
 * In-memory singleton for storing the JWT access token.
 * Kept in memory (NOT localStorage) to reduce XSS attack surface.
 * On page reload the token is gone; the app bootstraps via refresh token instead.
 */
// TODO: (HACK) token en memoria se pierde al recargar la página; considerar sessionStorage cifrado si el UX lo requiere
let _token: string | null = null;

export const tokenStore = {
  get(): string | null {
    return _token;
  },
  set(token: string): void {
    _token = token;
  },
  clear(): void {
    _token = null;
  },
};
