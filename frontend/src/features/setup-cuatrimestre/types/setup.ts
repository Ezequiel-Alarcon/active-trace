export interface SetupState {
  step: number;
  cohorte: { nombre: string; carrera: string; anio: string };
  clonar: { origen: string; destino: string };
  programas: { archivos: string[] };
  fechas: { inicio: string; fin: string; evaluaciones: string };
  aviso: { titulo: string; cuerpo: string };
  resumen: string[];
}

export const PASOS = [
  'Crear cohorte',
  'Clonar equipo',
  'Ajustar asignaciones',
  'Ajustar vigencias',
  'Cargar programas',
  'Cargar fechas',
  'Publicar aviso',
] as const;

export type SetupAction =
  | { type: 'SET_STEP'; step: number }
  | { type: 'NEXT' }
  | { type: 'PREV' }
  | { type: 'SET_COHORTE'; data: SetupState['cohorte'] }
  | { type: 'SET_CLONAR'; data: SetupState['clonar'] }
  | { type: 'SET_PROGRAMAS'; data: SetupState['programas'] }
  | { type: 'SET_FECHAS'; data: SetupState['fechas'] }
  | { type: 'SET_AVISO'; data: SetupState['aviso'] }
  | { type: 'ADD_RESUMEN'; item: string }
  | { type: 'RESET' };

export const INITIAL_SETUP_STATE: SetupState = {
  step: 0,
  cohorte: { nombre: '', carrera: '', anio: '' },
  clonar: { origen: '', destino: '' },
  programas: { archivos: [] },
  fechas: { inicio: '', fin: '', evaluaciones: '' },
  aviso: { titulo: '', cuerpo: '' },
  resumen: [],
};

export function setupReducer(state: SetupState, action: SetupAction): SetupState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, step: action.step };
    case 'NEXT':
      return { ...state, step: Math.min(state.step + 1, PASOS.length) };
    case 'PREV':
      return { ...state, step: Math.max(state.step - 1, 0) };
    case 'SET_COHORTE':
      return { ...state, cohorte: action.data };
    case 'SET_CLONAR':
      return { ...state, clonar: action.data };
    case 'SET_PROGRAMAS':
      return { ...state, programas: action.data };
    case 'SET_FECHAS':
      return { ...state, fechas: action.data };
    case 'SET_AVISO':
      return { ...state, aviso: action.data };
    case 'ADD_RESUMEN':
      return { ...state, resumen: [...state.resumen, action.item] };
    case 'RESET':
      return INITIAL_SETUP_STATE;
    default:
      return state;
  }
}
