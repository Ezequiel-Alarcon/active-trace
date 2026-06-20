import axios from 'axios';
import { describe, expect, it } from 'vitest';
import {
  PROFESSOR_DEMO_EQUIPOS,
  installProfessorDemoMocks,
  isProfessorDemoMocksEnabled,
} from './professorDemo';

function createClient() {
  const client = axios.create({ baseURL: 'http://localhost:8000' });
  client.defaults.adapter = async (config) => ({
    data: { passthrough: true, url: config.url },
    status: 200,
    statusText: 'OK',
    headers: {},
    config,
  });
  return client;
}

describe('professor demo mocks', () => {
  it('intercepts mis equipos with professor fixtures', async () => {
    const client = createClient();

    installProfessorDemoMocks(client);

    const response = await client.get('/api/equipos/mis-equipos');

    expect(response.data).toEqual(PROFESSOR_DEMO_EQUIPOS);
  });

  it('passes unrelated requests through the existing adapter', async () => {
    const client = createClient();

    installProfessorDemoMocks(client);

    const response = await client.get('/api/alumno/estado');

    expect(response.data).toEqual({ passthrough: true, url: '/api/alumno/estado' });
  });

  it('only enables the demo layer when the env flag is true', () => {
    expect(isProfessorDemoMocksEnabled({ VITE_ENABLE_PROFESSOR_DEMO_MOCKS: 'true' })).toBe(true);
    expect(isProfessorDemoMocksEnabled({ VITE_ENABLE_PROFESSOR_DEMO_MOCKS: 'false' })).toBe(false);
    expect(isProfessorDemoMocksEnabled({})).toBe(false);
  });
});
