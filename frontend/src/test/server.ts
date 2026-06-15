import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Initial handlers — provide sensible defaults to avoid noise in tests
// Individual tests override these via server.use(...)
export const handlers = [
  // Default: refresh returns 401 (no active session) — prevents AggregateError noise
  http.post('http://localhost:8000/api/auth/refresh', () =>
    HttpResponse.json({ code: 'AUTH_TOKEN_EXPIRED' }, { status: 401 }),
  ),
];

export const server = setupServer(...handlers);

// Re-export helpers for convenience in tests
export { http, HttpResponse };
