import type {
  CrawlJob,
  DocumentDetail,
  SearchResponse,
  StatsResponse,
} from "../types/api";

const TOKEN_KEY = "searchforge_admin_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiRequestError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail ? String(body.detail) : message;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiRequestError(message, res.status);
  }

  return res.json() as Promise<T>;
}

export function search(
  q: string,
  page: number,
  limit: number,
  mode: "tfidf" | "bm25" = "bm25"
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q, page: String(page), limit: String(limit), mode });
  return request<SearchResponse>(`/api/v1/search?${params.toString()}`);
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/api/v1/documents/${id}`);
}

export function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>(`/api/v1/stats`);
}

export function login(username: string, password: string): Promise<{ access_token: string; role: string }> {
  return request(`/api/v1/auth/login`, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function startCrawl(seed_url: string, max_pages: number, max_depth: number): Promise<CrawlJob> {
  return request<CrawlJob>(`/api/v1/crawl`, {
    method: "POST",
    body: JSON.stringify({ seed_url, max_pages, max_depth }),
  });
}

export function getCrawlJob(id: string): Promise<CrawlJob> {
  return request<CrawlJob>(`/api/v1/crawl/${id}`);
}

export function rebuildIndex(): Promise<{ status: string; documents_indexed: number }> {
  return request(`/api/v1/admin/index/rebuild`, { method: "POST" });
}

export function clearCache(): Promise<{ status: string; keys_cleared: number }> {
  return request(`/api/v1/admin/cache/clear`, { method: "POST" });
}
