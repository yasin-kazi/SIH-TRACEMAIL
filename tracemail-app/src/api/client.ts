const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function upload<T>(path: string, file: File): Promise<T> {
  const data = new FormData();
  data.append('file', file);
  return request<T>(path, { method: 'POST', body: data });
}
