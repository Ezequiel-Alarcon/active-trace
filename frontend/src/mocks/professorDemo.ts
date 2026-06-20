import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

export const PROFESSOR_DEMO_EQUIPOS = [
  {
    id: 'eq-prof-1',
    materia_id: 'mat-aed',
    materia_nombre: 'Algoritmos y Estructuras de Datos',
    carrera: 'Tecnicatura Universitaria en Programacion',
    cohorte: '2026',
    comisiones: ['Comision A'],
    rol: 'PROFESOR',
    docente_id: 'usr-profesor',
    docente_nombre: 'Profesor Demo',
    vigencia_desde: '2026-03-01',
    vigencia_hasta: '',
    estado: 'activo',
  },
  {
    id: 'eq-prof-2',
    materia_id: 'mat-poo',
    materia_nombre: 'Programacion Orientada a Objetos',
    carrera: 'Tecnicatura Universitaria en Programacion',
    cohorte: '2026',
    comisiones: ['Comision A', 'Laboratorio 2'],
    rol: 'PROFESOR',
    docente_id: 'usr-profesor',
    docente_nombre: 'Profesor Demo',
    vigencia_desde: '2026-03-01',
    vigencia_hasta: '',
    estado: 'activo',
  },
  {
    id: 'eq-prof-3',
    materia_id: 'mat-bd',
    materia_nombre: 'Base de Datos',
    carrera: 'Tecnicatura Universitaria en Programacion',
    cohorte: '2026',
    comisiones: ['Mesa intensiva'],
    rol: 'PROFESOR',
    docente_id: 'usr-profesor',
    docente_nombre: 'Profesor Demo',
    vigencia_desde: '2026-03-01',
    vigencia_hasta: '2026-05-31',
    estado: 'vencido',
  },
] as const;

type DemoEnv = Record<string, string | boolean | undefined>;

interface MockResponse {
  data: unknown;
  status?: number;
}

function buildMockAxiosResponse(
  config: InternalAxiosRequestConfig,
  mock: MockResponse,
): AxiosResponse {
  return {
    data: mock.data,
    status: mock.status ?? 200,
    statusText: 'OK',
    headers: {},
    config,
  };
}

function resolveProfessorDemoMock(
  config: Pick<InternalAxiosRequestConfig, 'method' | 'url'>,
): MockResponse | null {
  const method = (config.method ?? 'get').toLowerCase();
  const url = config.url ?? '';

  if (method === 'get' && url.startsWith('/api/equipos/mis-equipos')) {
    return { data: PROFESSOR_DEMO_EQUIPOS };
  }

  return null;
}

export function isProfessorDemoMocksEnabled(
  env: DemoEnv = import.meta.env as DemoEnv,
): boolean {
  return env.VITE_ENABLE_PROFESSOR_DEMO_MOCKS === 'true';
}

export function installProfessorDemoMocks(client: AxiosInstance): void {
  client.interceptors.request.use((config) => {
    const mock = resolveProfessorDemoMock(config);
    if (!mock) {
      return config;
    }

    // Keep this opt-in and local to the selected demo endpoints.
    config.adapter = async () => buildMockAxiosResponse(config, mock);
    return config;
  });
}
