import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

function makeWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <MemoryRouter>{children}</MemoryRouter>;
  };
}

describe('useReset', () => {
  it('6.6 — 200 → success=true', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/reset', () =>
        HttpResponse.json({}, { status: 200 }),
      ),
    );
    const { useReset } = await import('./useReset');
    const { result } = renderHook(() => useReset(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.submit({ token: 'valid-tok', new_password: 'NewPass1!' });
    });

    await waitFor(() => expect(result.current.success).toBe(true));
    expect(result.current.error).toBeNull();
  });

  it('6.6 — AUTH_RESET_EXPIRED shows recoverable error with link to forgot', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/reset', () =>
        HttpResponse.json({ code: 'AUTH_RESET_EXPIRED', message: 'Expired' }, { status: 401 }),
      ),
    );
    const { useReset } = await import('./useReset');
    const { result } = renderHook(() => useReset(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.submit({ token: 'expired-tok', new_password: 'NewPass1!' });
    });

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain('expiró');
    expect(result.current.success).toBe(false);
  });

  it('6.6 — AUTH_RESET_INVALID shows recoverable error', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/reset', () =>
        HttpResponse.json({ code: 'AUTH_RESET_INVALID', message: 'Invalid' }, { status: 401 }),
      ),
    );
    const { useReset } = await import('./useReset');
    const { result } = renderHook(() => useReset(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.submit({ token: 'invalid-tok', new_password: 'NewPass1!' });
    });

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain('expiró');
  });
});
