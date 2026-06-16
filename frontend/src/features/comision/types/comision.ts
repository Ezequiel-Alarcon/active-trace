/**
 * Types for the comision (workspace) feature.
 * Mirrors backend structures from C-10 / C-11.
 */

export interface Comision {
  id: string;
  materia_id: string;
  materia_nombre: string;
  cohorte_id: string;
  cohorte_nombre: string;
}

export interface ComisionSelectorState {
  comisionId: string | null;
}
