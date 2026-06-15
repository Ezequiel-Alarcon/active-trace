import { describe, it, expect, beforeEach } from 'vitest';
import { tokenStore } from './tokenStore';

describe('tokenStore', () => {
  beforeEach(() => {
    tokenStore.clear();
  });

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
