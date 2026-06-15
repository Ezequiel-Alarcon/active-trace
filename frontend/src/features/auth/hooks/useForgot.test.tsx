import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';

describe('useForgot', () => {
  it('6.5 — always shows neutral message on 200', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/forgot', () =>
        HttpResponse.json({}, { status: 200 }),
      ),
    );
    const { useForgot } = await import('./useForgot');
    const { result } = renderHook(() => useForgot());

    await act(async () => {
      await result.current.submit({ tenant_codigo: 'acme', email: 'exists@test.com' });
    });

    await waitFor(() => expect(result.current.submitted).toBe(true));
    expect(result.current.error).toBeNull();
  });

  it('6.5 — shows the same neutral message when email does NOT exist (still 200 per backend non-enumeration)', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/forgot', () =>
        HttpResponse.json({}, { status: 200 }),
      ),
    );
    const { useForgot } = await import('./useForgot');
    const { result } = renderHook(() => useForgot());

    await act(async () => {
      await result.current.submit({ tenant_codigo: 'acme', email: 'noexists@test.com' });
    });

    await waitFor(() => expect(result.current.submitted).toBe(true));
    // Both scenarios result in submitted=true — identical outcome
    expect(result.current.error).toBeNull();
  });

  it('6.5 — shows submitted even when backend errors (no account enumeration via errors)', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/forgot', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    const { useForgot } = await import('./useForgot');
    const { result } = renderHook(() => useForgot());

    await act(async () => {
      await result.current.submit({ tenant_codigo: 'acme', email: 'any@test.com' });
    });

    await waitFor(() => expect(result.current.submitted).toBe(true));
  });
});
