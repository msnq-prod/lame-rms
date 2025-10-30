export interface IntegrationSummary {
  name: string;
  description: string;
}

export interface IntegrationTaskStatus {
  id: string;
  state: string;
  status?: string | null;
  result?: Record<string, unknown> | null;
}

const API_BASE = process.env.VITE_API_BASE ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {"Content-Type": "application/json"},
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function listIntegrations(): Promise<IntegrationSummary[]> {
  return request<IntegrationSummary[]>("/integrations");
}

export async function enqueueIntegration(name: string): Promise<{task_id: string}> {
  return request<{task_id: string}>(`/integrations/${name}/enqueue`, {method: "POST"});
}

export async function integrationProgress(taskId: string): Promise<IntegrationTaskStatus> {
  return request<IntegrationTaskStatus>(`/integrations/tasks/${taskId}`);
}
