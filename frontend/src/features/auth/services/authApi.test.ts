import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';
import { tokenStore } from '../.././../shared/services/tokenStore';
import { login, verify2fa, forgotPassword, resetPassword, logout, extractAuthErrorCode } from './authApi';

describe('authApi', () => {
  beforeEach(() => {
    tokenStore.clear();
  });

  describe('login', () => {
    it('returns access_token on 200', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/login', () =>
          HttpResponse.json({ access_token: 'tok-123', token_type: 'bearer' }),
        ),
      );
      const result = await login({ tenant_codigo: 'acme', email: 'a@b.com', password: 'p' });
      expect(result.access_token).toBe('tok-123');
    });

    it('throws on 401 with code AUTH_INVALID_CREDENTIALS', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/login', () =>
          HttpResponse.json({ code: 'AUTH_INVALID_CREDENTIALS', message: 'Bad credentials' }, { status: 401 }),
        ),
      );
      let code: string | null = null;
      try {
        await login({ tenant_codigo: 'acme', email: 'a@b.com', password: 'wrong' });
      } catch (err) {
        code = extractAuthErrorCode(err);
      }
      expect(code).toBe('AUTH_INVALID_CREDENTIALS');
    });

    it('throws on 401 with code AUTH_2FA_REQUIRED', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/login', () =>
          HttpResponse.json({ code: 'AUTH_2FA_REQUIRED', message: '2FA required' }, { status: 401 }),
        ),
      );
      let code: string | null = null;
      try {
        await login({ tenant_codigo: 'acme', email: 'a@b.com', password: 'p' });
      } catch (err) {
        code = extractAuthErrorCode(err);
      }
      expect(code).toBe('AUTH_2FA_REQUIRED');
    });
  });

  describe('verify2fa', () => {
    it('returns access_token on 200', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/2fa/verify', () =>
          HttpResponse.json({ access_token: 'tok-2fa', token_type: 'bearer' }),
        ),
      );
      const result = await verify2fa({ tenant_codigo: 'acme', email: 'a@b.com', password: 'p', totp_code: '123456' });
      expect(result.access_token).toBe('tok-2fa');
    });

    it('throws on 401 with code AUTH_2FA_INVALID', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/2fa/verify', () =>
          HttpResponse.json({ code: 'AUTH_2FA_INVALID', message: 'Invalid code' }, { status: 401 }),
        ),
      );
      let code: string | null = null;
      try {
        await verify2fa({ tenant_codigo: 'acme', email: 'a@b.com', password: 'p', totp_code: '000000' });
      } catch (err) {
        code = extractAuthErrorCode(err);
      }
      expect(code).toBe('AUTH_2FA_INVALID');
    });
  });

  describe('forgotPassword', () => {
    it('resolves without error on 200', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/forgot', () =>
          HttpResponse.json({}, { status: 200 }),
        ),
      );
      await expect(forgotPassword({ tenant_codigo: 'acme', email: 'a@b.com' })).resolves.toBeUndefined();
    });
  });

  describe('resetPassword', () => {
    it('resolves without error on 200', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/reset', () =>
          HttpResponse.json({}, { status: 200 }),
        ),
      );
      await expect(resetPassword({ token: 'reset-tok', new_password: 'Passw0rd!' })).resolves.toBeUndefined();
    });

    it('throws on 401 with code AUTH_RESET_EXPIRED', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/reset', () =>
          HttpResponse.json({ code: 'AUTH_RESET_EXPIRED', message: 'Link expired' }, { status: 401 }),
        ),
      );
      let code: string | null = null;
      try {
        await resetPassword({ token: 'old-tok', new_password: 'Passw0rd!' });
      } catch (err) {
        code = extractAuthErrorCode(err);
      }
      expect(code).toBe('AUTH_RESET_EXPIRED');
    });
  });

  describe('logout', () => {
    it('resolves without error on 204', async () => {
      server.use(
        http.post('http://localhost:8000/api/auth/logout', () =>
          new HttpResponse(null, { status: 204 }),
        ),
      );
      await expect(logout()).resolves.toBeUndefined();
    });
  });
});
