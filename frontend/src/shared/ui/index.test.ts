import { describe, it, expect } from 'vitest';
import * as ui from './index';

describe('barrel @/shared/ui', () => {
  it('2.10 — expone todos los primitivos y helpers desde un único punto', () => {
    const exportados = [
      'Button',
      'Badge',
      'StatusBadge',
      'Card',
      'PageHeader',
      'EmptyState',
      'KpiCard',
      'FilterBar',
      'DataTable',
      'clasesEstado',
    ];
    for (const nombre of exportados) {
      expect(ui).toHaveProperty(nombre);
    }
  });
});
