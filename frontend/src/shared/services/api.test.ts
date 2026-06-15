import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from '../../../src/test/server';
import { server } from '../../../src/test/server';
import { tokenStore } from './tokenStore';

// Import api lazily to capture its state after tokenStore is configured
let capturedAuthHeader: string | null = null;

describe('api — request interceptor', () => {
  beforeEach(() => {
    tokenStore.clear();
    capturedAuthHeader = null;
  });

  it('attaches Authorization header when a token is in the store', async () => {
    tokenStore.set('test-access-token');

    server.use(
      http.get('http://localhost:8000/api/data', ({ request }) => {
        capturedAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({ ok: true });
      }),
    );

    const { apiClient } = await import('./api');
    await apiClient.get('/api/data');

    expect(capturedAuthHeader).toBe('Bearer test-access-token');
  });

  it('does NOT attach Authorization header when no token in the store', async () => {
    // tokenStore already cleared in beforeEach
    server.use(
      http.get('http://localhost:8000/api/data-anon', ({ request }) => {
        capturedAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({ ok: true });
      }),
    );

    const { apiClient } = await import('./api');
    await apiClient.get('/api/data-anon');

    expect(capturedAuthHeader).toBeNull();
  });

  it('does NOT attach token to /api/auth/login even when a stale token exists', async () => {
    tokenStore.set('stale-token');

    server.use(
      http.post('http://localhost:8000/api/auth/login', ({ request }) => {
        capturedAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({ access_token: 'new-token' });
      }),
    );

    const { apiClient } = await import('./api');
    await apiClient.post('/api/auth/login', {});

    expect(capturedAuthHeader).toBeNull();
  });

  it('does NOT attach token to /api/auth/forgot even when a stale token exists', async () => {
    tokenStore.set('stale-token');

    server.use(
      http.post('http://localhost:8000/api/auth/forgot', ({ request }) => {
        capturedAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({});
      }),
    );

    const { apiClient } = await import('./api');
    await apiClient.post('/api/auth/forgot', {});

    expect(capturedAuthHeader).toBeNull();
  });

  it('does NOT attach token to /api/auth/reset even when a stale token exists', async () => {
    tokenStore.set('stale-token');

    server.use(
      http.post('http://localhost:8000/api/auth/reset', ({ request }) => {
        capturedAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({});
      }),
    );

    const { apiClient } = await import('./api');
    await apiClient.post('/api/auth/reset', {});

    expect(capturedAuthHeader).toBeNull();
  });
});
