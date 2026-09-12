import type {
  BatchExportResult,
  CharacterAsset,
  ExportBundle,
  ExportOptions,
  GenerateResponse,
  ImportResponse,
  Manifest,
  Meta,
} from './types';

const BASE = '';

async function json<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + input, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === 'string' ? body.detail : JSON.stringify(body?.detail ?? body);
    } catch {
      /* ignora */
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return (await res.json()) as T;
}

export const api = {
  meta: () => json<Meta>('/api/meta'),

  generate: (payload: unknown) =>
    json<GenerateResponse>('/api/characters/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  importImage: (form: FormData) =>
    json<ImportResponse>('/api/characters/import', { method: 'POST', body: form }),

  list: () => json<CharacterAsset[]>('/api/characters'),

  get: (id: string) => json<CharacterAsset>(`/api/characters/${id}`),

  remove: (id: string) => json<{ deleted: boolean }>(`/api/characters/${id}`, { method: 'DELETE' }),

  manifest: (id: string) => json<Manifest>(`/api/characters/${id}/manifest.json`),

  exportBatch: (payload: { ids: string[] | null; options: ExportOptions }) =>
    json<BatchExportResult>('/api/characters/export-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  export: (id: string, options: ExportOptions) =>
    json<ExportBundle>(`/api/characters/${id}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    }),
};

export function thumbUrl(id: string, direction = 'down', scale = 3): string {
  return `${BASE}/api/characters/${id}/pose.png?direction=${direction}&scale=${scale}`;
}

export function sheetUrl(id: string, scale = 1): string {
  return `${BASE}/api/characters/${id}/sheet.png?scale=${scale}`;
}

export function manifestUrl(id: string): string {
  return `${BASE}/api/characters/${id}/manifest.json`;
}
