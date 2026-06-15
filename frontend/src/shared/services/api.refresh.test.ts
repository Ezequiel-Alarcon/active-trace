import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from '../../../src/test/server';
import { server } from '../../../src/test/server';
import { tokenStore } from './tokenStore';
import { setLogoutCallback } from './api';

describe('api — response interceptor: transparent refresh', () => {
  beforeEach(() => {
    tokenStore.clear();
    setLogoutCallback(() => undefined);
  });

  // ── Task 4.1: Single 401 triggers refresh + retry ──────────────────────

  it('4.1 — 401 triggers refresh; caller receives the retried 200, never the 401', async () => {
    tokenStore.set('expired-token');

    let refreshCallCount = 0;

    server.use(
      http.get('http://localhost:8000/api/protected', () => {
        const token = tokenStore.get();
        if (token === 'expired-token') {
          return HttpResponse.json({ code: 'AUTH_TOKEN_EXPIRED' }, { status: 401 });
        }
        return HttpResponse.json({ data: 'secret' });
      }),
      http.post('http://localhost:8000/api/auth/refresh', () => {
        refreshCallCount++;
        tokenStore.set('new-token');
        return HttpResponse.json({ access_token: 'new-token' });
      }),
    );

    const { apiClient } = await import('./api');
    const response = await apiClient.get('/api/protected');

    expect(response.status).toBe(200);
    expect(response.data).toEqual({ data: 'secret' });
    expect(refreshCallCount).toBe(1);
    expect(tokenStore.get()).toBe('new-token');
  });

  // ── Task 4.2: Single-flight — N concurrent 401s → exactly 1 refresh ───

  it('4.2 — 3 concurrent 401s trigger EXACTLY one POST /api/auth/refresh (single-flight)', async () => {
    tokenStore.set('expired-token');

    let refreshCallCount = 0;

    server.use(
      http.get('http://localhost:8000/api/r1', () => {
        if (tokenStore.get() === 'expired-token') {
          return HttpResponse.json({}, { status: 401 });
        }
        return HttpResponse.json({ resource: 1 });
      }),
      http.get('http://localhost:8000/api/r2', () => {
        if (tokenStore.get() === 'expired-token') {
          return HttpResponse.json({}, { status: 401 });
        }
        return HttpResponse.json({ resource: 2 });
      }),
      http.get('http://localhost:8000/api/r3', () => {
        if (tokenStore.get() === 'expired-token') {
          return HttpResponse.json({}, { status: 401 });
        }
        return HttpResponse.json({ resource: 3 });
      }),
      http.post('http://localhost:8000/api/auth/refresh', async () => {
        refreshCallCount++;
        // Small delay to let concurrent requests queue
        await new Promise((r) => setTimeout(r, 20));
        tokenStore.set('new-token-sf');
        return HttpResponse.json({ access_token: 'new-token-sf' });
      }),
    );

    const { apiClient } = await import('./api');

    const [r1, r2, r3] = await Promise.all([
      apiClient.get('/api/r1'),
      apiClient.get('/api/r2'),
      apiClient.get('/api/r3'),
    ]);

    expect(refreshCallCount).toBe(1);
    expect(r1.status).toBe(200);
    expect(r2.status).toBe(200);
    expect(r3.status).toBe(200);
    expect(tokenStore.get()).toBe('new-token-sf');
  });

  // ── Task 4.3: Refresh fails → clear token + logout callback ────────────

  it('4.3 — refresh 401 → token store cleared and logout callback invoked', async () => {
    tokenStore.set('totally-expired');

    const logoutSpy = vi.fn();
    setLogoutCallback(logoutSpy);

    server.use(
      http.get('http://localhost:8000/api/protected-fail', () => {
        return HttpResponse.json({}, { status: 401 });
      }),
      http.post('http://localhost:8000/api/auth/refresh', () => {
        return HttpResponse.json({ code: 'AUTH_TOKEN_REVOKED' }, { status: 401 });
      }),
    );

    const { apiClient } = await import('./api');

    await expect(apiClient.get('/api/protected-fail')).rejects.toThrow();

    expect(tokenStore.get()).toBeNull();
    expect(logoutSpy).toHaveBeenCalledOnce();
  });

  // ── Task 4.4: 403 → no refresh, no retry, error propagated ────────────

  it('4.4 — 403 is surfaced directly without refresh or retry', async () => {
    tokenStore.set('valid-token');

    let refreshCallCount = 0;
    let requestCount = 0;

    server.use(
      http.get('http://localhost:8000/api/forbidden', () => {
        requestCount++;
        return HttpResponse.json({ code: 'FORBIDDEN' }, { status: 403 });
      }),
      http.post('http://localhost:8000/api/auth/refresh', () => {
        refreshCallCount++;
        return HttpResponse.json({ access_token: 'should-not-be-called' });
      }),
    );

    const { apiClient } = await import('./api');

    let caughtStatus: number | undefined;
    try {
      await apiClient.get('/api/forbidden');
    } catch (err) {
      const axiosErr = err as import('axios').AxiosError;
      caughtStatus = axiosErr.response?.status;
    }

    expect(caughtStatus).toBe(403);
    expect(refreshCallCount).toBe(0);
    expect(requestCount).toBe(1); // no retry
  });
});
