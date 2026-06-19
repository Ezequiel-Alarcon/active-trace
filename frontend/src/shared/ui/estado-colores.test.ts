import { describe, it, expect } from 'vitest';
import { clasesEstado } from './estado-colores';

describe('clasesEstado', () => {
  it('1.1 — atrasado resuelve a rojo', () => {
    expect(clasesEstado('atrasado')).toBe('bg-red-100 text-red-700');
  });

  it('1.1 — aprobado resuelve a verde', () => {
    expect(clasesEstado('aprobado')).toBe('bg-green-100 text-green-700');
  });

  it('1.1 — pendiente resuelve a ámbar', () => {
    expect(clasesEstado('pendiente')).toBe('bg-amber-100 text-amber-700');
  });

  it('1.1 — en-envio resuelve a azul', () => {
    expect(clasesEstado('en-envio')).toBe('bg-blue-100 text-blue-700');
  });

  it('1.1 — pendiente-cola resuelve a gris (distinto de pendiente/ámbar)', () => {
    expect(clasesEstado('pendiente-cola')).toBe('bg-gray-100 text-gray-700');
    expect(clasesEstado('pendiente-cola')).not.toBe(clasesEstado('pendiente'));
  });

  it('1.1 — consistencia: estados del mismo grupo comparten color', () => {
    // aprobado y enviado son ambos verde; atrasado y fallido son ambos rojo;
    // pendiente y cancelado son ambos ámbar.
    expect(clasesEstado('aprobado')).toBe(clasesEstado('enviado'));
    expect(clasesEstado('atrasado')).toBe(clasesEstado('fallido'));
    expect(clasesEstado('pendiente')).toBe(clasesEstado('cancelado'));
  });

  it('1.1 — los 5 colores semánticos son distintos entre sí', () => {
    const colores = new Set([
      clasesEstado('atrasado'),
      clasesEstado('aprobado'),
      clasesEstado('pendiente'),
      clasesEstado('en-envio'),
      clasesEstado('neutro'),
    ]);
    expect(colores.size).toBe(5);
  });
});
