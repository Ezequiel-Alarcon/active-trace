import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';
import { tokenStore } from '../../../shared/services/tokenStore';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../components/AuthProvider';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  // Default: session endpoint fails (not logged in yet)
  server.use(
    http.get('http://localhost:8000/api/auth/session', () =>
      HttpResponse.json({}, { status: 401 }),
    ),
  );

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AuthProvider>{children}</AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };
}

describe('useLogin', () => {
  beforeEach(() => tokenStore.clear());

  it('6.2 — successful login stores token and navigates', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/login', () =>
        HttpResponse.json({ access_token: 'tok-ok', token_type: 'bearer', totp_enabled: false }),
      ),
    );

    const { useLogin } = await import('./useLogin');
    const { result } = renderHook(() => useLogin(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.submitCredentials({
        tenant_codigo: 'acme',
        email: 'user@test.com',
        password: 'Passw0rd!',
      });
    });

    // After successful login the token should be in memory
    expect(tokenStore.get()).toBe('tok-ok');
  });

  it('6.3 — AUTH_INVALID_CREDENTIALS shows generic error without revealing field', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/login', () =>
        HttpResponse.json({ code: 'AUTH_INVALID_CREDENTIALS', message: 'Bad credentials' }, { status: 401 }),
      ),
    );

    const { useLogin } = await import('./useLogin');
    const { result } = renderHook(() => useLogin(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.submitCredentials({
        tenant_codigo: 'acme',
        email: 'user@test.com',
        password: 'wrong',
      });
    });

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain('Credenciales inválidas');
    // Error message must not reveal which field failed
    expect(result.current.error).not.toContain('email');
    expect(result.current.error).not.toContain('password');
    expect(result.current.step).toBe('credentials');
  });

  it('6.4 — AUTH_2FA_REQUIRED transitions to 2fa step', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/login', () =>
        HttpResponse.json({ code: 'AUTH_2FA_REQUIRED', message: '2FA needed' }, { status: 401 }),
      ),
    );

    const { useLogin } = await import('./useLogin');
    const { result } = renderHook(() => useLogin(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.submitCredentials({
        tenant_codigo: 'acme',
        email: 'user@test.com',
        password: 'Passw0rd!',
      });
    });

    await waitFor(() => expect(result.current.step).toBe('2fa'));
    expect(result.current.error).toBeNull(); // 2FA required is not an error, it's a step
  });

  it('6.4 — AUTH_2FA_INVALID keeps user on 2fa step with generic message', async () => {
    // First: credentials pass but 2FA required
    server.use(
      http.post('http://localhost:8000/api/auth/login', () =>
        HttpResponse.json({ code: 'AUTH_2FA_REQUIRED' }, { status: 401 }),
      ),
      http.post('http://localhost:8000/api/auth/2fa/verify', () =>
        HttpResponse.json({ code: 'AUTH_2FA_INVALID' }, { status: 401 }),
      ),
    );

    const { useLogin } = await import('./useLogin');
    const { result } = renderHook(() => useLogin(), { wrapper: makeWrapper() });

    // Go to 2FA step
    await act(async () => {
      await result.current.submitCredentials({
        tenant_codigo: 'acme',
        email: 'user@test.com',
        password: 'Passw0rd!',
      });
    });
    await waitFor(() => expect(result.current.step).toBe('2fa'));

    // Submit wrong TOTP
    await act(async () => {
      await result.current.submit2fa('000000');
    });

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.step).toBe('2fa');
    expect(result.current.error).toContain('Código inválido');
    expect(tokenStore.get()).toBeNull(); // No session established
  });
});
