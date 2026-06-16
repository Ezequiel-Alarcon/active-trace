import { describe, it, expect, beforeEach } from 'vitest';
import { tokenStore } from './tokenStore';

describe('tokenStore', () => {
  beforeEach(() => {
    tokenStore.clear();
  });

  describe('access token', () => {
    it('returns null when no token has been set', () => {
      expect(tokenStore.get()).toBeNull();
    });

    it('set → get returns the stored token', () => {
      tokenStore.set('abc.def.ghi');
      expect(tokenStore.get()).toBe('abc.def.ghi');
    });

    it('clear → get returns null', () => {
      tokenStore.set('abc.def.ghi');
      tokenStore.clear();
      expect(tokenStore.get()).toBeNull();
    });

    it('overwriting the token replaces the previous value', () => {
      tokenStore.set('first-token');
      tokenStore.set('second-token');
      expect(tokenStore.get()).toBe('second-token');
    });
  });

  describe('refresh token', () => {
    it('returns null when no refresh token has been set', () => {
      expect(tokenStore.getRefresh()).toBeNull();
    });

    it('setRefresh → getRefresh returns the stored token', () => {
      tokenStore.setRefresh('refresh.abc.xyz');
      expect(tokenStore.getRefresh()).toBe('refresh.abc.xyz');
    });

    it('clear → getRefresh returns null', () => {
      tokenStore.setRefresh('refresh.abc.xyz');
      tokenStore.clear();
      expect(tokenStore.getRefresh()).toBeNull();
    });

    it('clear wipes both access and refresh tokens', () => {
      tokenStore.set('access.tok');
      tokenStore.setRefresh('refresh.tok');
      tokenStore.clear();
      expect(tokenStore.get()).toBeNull();
      expect(tokenStore.getRefresh()).toBeNull();
    });

    it('overwriting the refresh token replaces the previous value', () => {
      tokenStore.setRefresh('first-refresh');
      tokenStore.setRefresh('second-refresh');
      expect(tokenStore.getRefresh()).toBe('second-refresh');
    });
  });
});
