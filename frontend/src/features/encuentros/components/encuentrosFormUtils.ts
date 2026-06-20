import type { AxiosError } from 'axios';
import type { Path, UseFormSetError } from 'react-hook-form';
import type {
  CreateInstanciaUnicaRequest,
  CreateSlotRequest,
  InstanciaUnicaFormValues,
  ModalidadEncuentro,
  SlotFormValues,
} from '../types/encuentros';

export const SLOT_WIZARD_STORAGE_KEY = 'encuentros-slot-wizard';

interface ApiValidationIssue {
  loc?: Array<string | number>;
  msg?: string;
}

interface ApiValidationErrorResponse {
  detail?: ApiValidationIssue[] | string;
}

export interface StoredSlotWizardState {
  step: number;
  values: SlotFormValues;
}

export const DAY_OPTIONS = [
  { value: 0, label: 'Lunes' },
  { value: 1, label: 'Martes' },
  { value: 2, label: 'Miércoles' },
  { value: 3, label: 'Jueves' },
  { value: 4, label: 'Viernes' },
  { value: 5, label: 'Sábado' },
  { value: 6, label: 'Domingo' },
];

export const MODALIDAD_OPTIONS: Array<{ value: ModalidadEncuentro; label: string }> = [
  { value: 'presencial', label: 'Presencial' },
  { value: 'meet', label: 'Virtual por Meet' },
  { value: 'video', label: 'Video grabado' },
];

export function getTodayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export function getDefaultSlotFormValues(): SlotFormValues {
  return {
    materia_id: '',
    cohorte_id: '',
    titulo: '',
    dia_semana: 0,
    hora_inicio: '',
    hora_fin: '',
    fecha_inicio: getTodayIsoDate(),
    cant_semanas: 16,
    modalidad: 'presencial',
    link: '',
  };
}

export function getDefaultInstanciaUnicaFormValues(): InstanciaUnicaFormValues {
  return {
    materia_id: '',
    cohorte_id: '',
    fecha: getTodayIsoDate(),
    hora_inicio: '',
    hora_fin: '',
    titulo: '',
    modalidad: 'presencial',
    link: '',
    comentario: '',
  };
}

function buildUrls(modalidad: ModalidadEncuentro, link: string) {
  const normalizedLink = link.trim() || null;

  if (modalidad === 'meet') {
    return { meet_url: normalizedLink, video_url: null };
  }

  if (modalidad === 'video') {
    return { meet_url: null, video_url: normalizedLink };
  }

  return { meet_url: null, video_url: null };
}

export function toCreateSlotRequest(values: SlotFormValues): CreateSlotRequest {
  return {
    materia_id: values.materia_id,
    cohorte_id: values.cohorte_id,
    titulo: values.titulo.trim(),
    dia_semana: Number(values.dia_semana),
    hora_inicio: values.hora_inicio,
    hora_fin: values.hora_fin,
    fecha_inicio: values.fecha_inicio,
    cant_semanas: Number(values.cant_semanas),
    ...buildUrls(values.modalidad, values.link),
  };
}

export function toCreateInstanciaUnicaRequest(
  values: InstanciaUnicaFormValues,
): CreateInstanciaUnicaRequest {
  return {
    materia_id: values.materia_id,
    cohorte_id: values.cohorte_id,
    fecha: values.fecha,
    hora_inicio: values.hora_inicio,
    hora_fin: values.hora_fin,
    titulo: values.titulo.trim(),
    comentario: values.comentario?.trim() ? values.comentario.trim() : null,
    ...buildUrls(values.modalidad, values.link),
  };
}

export function loadStoredSlotWizardState(): StoredSlotWizardState | null {
  const raw = window.sessionStorage.getItem(SLOT_WIZARD_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as StoredSlotWizardState;
    if (!parsed || typeof parsed.step !== 'number' || !parsed.values) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveStoredSlotWizardState(state: StoredSlotWizardState) {
  window.sessionStorage.setItem(SLOT_WIZARD_STORAGE_KEY, JSON.stringify(state));
}

export function clearStoredSlotWizardState() {
  window.sessionStorage.removeItem(SLOT_WIZARD_STORAGE_KEY);
}

export function applyValidationErrors<TFieldValues extends Record<string, unknown>>(
  error: unknown,
  setError: UseFormSetError<TFieldValues>,
  aliases: Partial<Record<string, Path<TFieldValues>>> = {},
) {
  const axiosError = error as AxiosError<ApiValidationErrorResponse>;
  const detail = axiosError.response?.data?.detail;

  if (!axiosError.response || axiosError.response.status !== 422 || !Array.isArray(detail)) {
    return false;
  }

  for (const issue of detail) {
    const rawField = typeof issue.loc?.[1] === 'string' ? issue.loc[1] : null;
    const message = issue.msg?.trim();
    if (!rawField || !message) {
      continue;
    }

    const field = aliases[rawField] ?? (rawField as Path<TFieldValues>);
    setError(field, { type: 'server', message });
  }

  return true;
}
