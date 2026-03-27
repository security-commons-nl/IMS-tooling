import { getToken, clearToken } from './auth';
import { API_BASE_URL } from './constants';
import type {
  TokenResponse,
  DevTokenRequest,
  CurrentUser,
  StepResponse,
  StepExecutionResponse,
  StepDependencyResponse,
  DecisionResponse,
  DocumentResponse,
  DocumentVersionResponse,
  SetupScoreResponse,
} from './api-types';

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API Error ${status}`);
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new ApiError(401, 'Unauthorized');
  }

  if (!res.ok) {
    throw new ApiError(res.status, await res.json().catch(() => null));
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  auth: {
    devToken: (data: DevTokenRequest) =>
      apiFetch<TokenResponse>('/auth/dev-token', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    me: () => apiFetch<CurrentUser>('/auth/me'),
  },
  steps: {
    list: () => apiFetch<StepResponse[]>('/steps/'),
    get: (id: string) => apiFetch<StepResponse>(`/steps/${id}`),
    listExecutions: () =>
      apiFetch<StepExecutionResponse[]>('/steps/executions/'),
    createExecution: (data: { step_id: string; status?: string }) =>
      apiFetch<StepExecutionResponse>('/steps/executions/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    updateExecution: (id: string, data: { status?: string; skipped?: boolean; skip_reason?: string }) =>
      apiFetch<StepExecutionResponse>(`/steps/executions/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    listDependencies: () =>
      apiFetch<StepDependencyResponse[]>('/steps/dependencies/'),
  },
  decisions: {
    list: () => apiFetch<DecisionResponse[]>('/decisions/'),
    create: (data: Record<string, unknown>) =>
      apiFetch<DecisionResponse>('/decisions/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
  documents: {
    list: () => apiFetch<DocumentResponse[]>('/documents/'),
    get: (id: string) => apiFetch<DocumentResponse>(`/documents/${id}`),
    create: (data: Record<string, unknown>) =>
      apiFetch<DocumentResponse>('/documents/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    listVersions: (docId: string) =>
      apiFetch<DocumentVersionResponse[]>(`/documents/${docId}/versions/`),
    createVersion: (docId: string, data: Record<string, unknown>) =>
      apiFetch<DocumentVersionResponse>(`/documents/${docId}/versions/`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
  scores: {
    setupScores: () => apiFetch<SetupScoreResponse[]>('/scores/setup-scores/'),
  },
};

export { apiFetch };
