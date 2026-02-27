const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) || DEFAULT_API_BASE_URL;

export class APIError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers,
  });

  const raw = await response.text();
  const payload = raw ? safeParse(raw) : null;

  if (!response.ok) {
    const detail = payload && typeof payload === "object" && "detail" in payload ? String(payload.detail) : response.statusText;
    throw new APIError(response.status, detail || "Request failed");
  }

  return payload as T;
}

function safeParse(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}
