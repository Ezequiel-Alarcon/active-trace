import { z } from 'zod';

export interface SlotResponse {
  id: string;
  materia_id: string;
  materia_nombre: string;
  dia: string;
  horario: string;
  fecha_inicio: string;
  cantidad_semanas: number;
  titulo: string;
  enlace: string;
}

export interface InstanciaResponse {
  id: string;
  materia_id: string;
  materia_nombre: string;
  docente_id: string;
  docente_nombre: string;
  dia: string;
  horario: string;
  enlace: string;
  estado: string;
  grabacion: string;
}

export interface GuardiaResponse {
  id: string;
  tutor_id: string;
  tutor_nombre: string;
  materia_id: string;
  materia_nombre: string;
  dia: string;
  horario: string;
  estado: string;
  comentarios: string;
}

export interface EncuentroFilters {
  materia?: string;
  docente?: string;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface CreateSlotRequest {
  materia_id: string;
  cohorte_id: string;
  titulo: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  fecha_inicio: string;
  cant_semanas: number;
  meet_url?: string | null;
  video_url?: string | null;
}

export interface CreateInstanciaUnicaRequest {
  materia_id: string;
  cohorte_id: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  titulo: string;
  meet_url?: string | null;
  video_url?: string | null;
  comentario?: string | null;
}

export interface CreatedSlotResponse {
  id: string;
  tenant_id: string;
  materia_id: string;
  cohorte_id: string;
  titulo: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  fecha_inicio: string;
  cant_semanas: number;
  meet_url: string | null;
  video_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreatedInstanciaUnicaResponse {
  id: string;
  tenant_id: string;
  slot_id: string | null;
  materia_id: string;
  cohorte_id: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  titulo: string;
  estado: string;
  meet_url: string | null;
  video_url: string | null;
  comentario: string | null;
  created_at: string;
  updated_at: string;
}

export type ModalidadEncuentro = 'presencial' | 'meet' | 'video';

const requiredIdSchema = z.string().min(1, 'Este campo es obligatorio');
const requiredTextSchema = z.string().trim().min(1, 'Este campo es obligatorio');
const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/, 'Ingresá una hora válida');
const optionalUrlSchema = z.union([
  z.literal(''),
  z.string().trim().url('Ingresá una URL válida'),
]);
const modalidadSchema = z.enum(['presencial', 'meet', 'video']);

function isTodayOrFuture(value: string) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const input = new Date(`${value}T00:00:00`);
  return !Number.isNaN(input.getTime()) && input >= today;
}

function validateTimeRange(
  horaInicio: string,
  horaFin: string,
  addIssue: (message: string, path: 'hora_fin') => void,
) {
  if (horaInicio && horaFin && horaFin <= horaInicio) {
    addIssue('La hora de fin debe ser mayor a la hora de inicio', 'hora_fin');
  }
}

function validateModalidadLink(
  modalidad: ModalidadEncuentro,
  link: string,
  addIssue: (message: string, path: 'link') => void,
) {
  if (modalidad !== 'presencial' && !link.trim()) {
    addIssue('El enlace es obligatorio para encuentros virtuales', 'link');
  }
}

export const createSlotRequestSchema = z.object({
  materia_id: requiredIdSchema,
  cohorte_id: requiredIdSchema,
  titulo: requiredTextSchema,
  dia_semana: z.coerce.number().int().min(0).max(6),
  hora_inicio: timeSchema,
  hora_fin: timeSchema,
  fecha_inicio: z.string().min(1, 'La fecha de inicio es obligatoria'),
  cant_semanas: z.coerce.number().int().min(1).max(52),
  meet_url: z.string().trim().url('Ingresá una URL válida').nullable().optional(),
  video_url: z.string().trim().url('Ingresá una URL válida').nullable().optional(),
});

export const createInstanciaUnicaRequestSchema = z.object({
  materia_id: requiredIdSchema,
  cohorte_id: requiredIdSchema,
  fecha: z.string().min(1, 'La fecha es obligatoria'),
  hora_inicio: timeSchema,
  hora_fin: timeSchema,
  titulo: requiredTextSchema,
  meet_url: z.string().trim().url('Ingresá una URL válida').nullable().optional(),
  video_url: z.string().trim().url('Ingresá una URL válida').nullable().optional(),
  comentario: z.string().trim().nullable().optional(),
});

export const slotFormSchema = z.object({
  materia_id: requiredIdSchema,
  cohorte_id: requiredIdSchema,
  titulo: requiredTextSchema,
  dia_semana: z.coerce.number({ invalid_type_error: 'Seleccioná un día' }).int().min(0).max(6),
  hora_inicio: timeSchema,
  hora_fin: timeSchema,
  fecha_inicio: z.string().min(1, 'La fecha de inicio es obligatoria'),
  cant_semanas: z.coerce
    .number({ invalid_type_error: 'Ingresá una cantidad válida' })
    .int()
    .min(1, 'La cantidad mínima es 1')
    .max(52, 'La cantidad máxima es 52'),
  modalidad: modalidadSchema,
  link: optionalUrlSchema,
}).superRefine((data, ctx) => {
  validateTimeRange(data.hora_inicio, data.hora_fin, (message, path) => {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message, path: [path] });
  });
  validateModalidadLink(data.modalidad, data.link, (message, path) => {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message, path: [path] });
  });
});

export const instanciaUnicaFormSchema = z.object({
  materia_id: requiredIdSchema,
  cohorte_id: requiredIdSchema,
  fecha: z.string().min(1, 'La fecha es obligatoria'),
  hora_inicio: timeSchema,
  hora_fin: timeSchema,
  titulo: requiredTextSchema,
  modalidad: modalidadSchema,
  link: optionalUrlSchema,
  comentario: z.string().trim().max(500, 'El comentario no puede superar 500 caracteres').optional(),
}).superRefine((data, ctx) => {
  validateTimeRange(data.hora_inicio, data.hora_fin, (message, path) => {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message, path: [path] });
  });
  validateModalidadLink(data.modalidad, data.link, (message, path) => {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message, path: [path] });
  });
  if (data.fecha && !isTodayOrFuture(data.fecha)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'La fecha no puede ser anterior a hoy',
      path: ['fecha'],
    });
  }
});

export type SlotFormValues = z.infer<typeof slotFormSchema>;
export type InstanciaUnicaFormValues = z.infer<typeof instanciaUnicaFormSchema>;
