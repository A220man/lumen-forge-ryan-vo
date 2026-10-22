const API_BASE = '/api/v1';

export interface Issue {
  id: number;
  title: string;
  body: string | null;
  html_url: string;
  state: 'open' | 'closed';
  labels: string[];
  assignees: string[];
  comments_count: number;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  author_login: string;
  author_html_url: string | null;
  repository: string;
  comments?: Comment[];
}

export interface Comment {
  user: { login: string };
  body: string;
  created_at: string;
}

export interface IssueListResponse {
  items: Issue[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Analysis {
  id: number;
  issue_id: number;
  summary: string;
  key_points: string[];
  blockers: string[];
  unresolved_questions: string[];
  provider: string;
  model: string;
  created_at: string;
  raw_response: string | null;
  advisory: boolean;
}

export interface SyncResponse {
  created: number;
  updated: number;
  errors: number;
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  issues: {
    list: (params?: {
      page?: number;
      page_size?: number;
      state?: 'open' | 'closed';
      search?: string;
      label?: string;
    }): Promise<IssueListResponse> => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', String(params.page));
      if (params?.page_size) searchParams.set('page_size', String(params.page_size));
      if (params?.state) searchParams.set('state', params.state);
      if (params?.search) searchParams.set('search', params.search);
      if (params?.label) searchParams.set('label', params.label);
      return fetchJson(`${API_BASE}/issues?${searchParams.toString()}`);
    },

    get: (id: number): Promise<Issue> =>
      fetchJson(`${API_BASE}/issues/${id}`),

    sync: (): Promise<SyncResponse> =>
      fetchJson(`${API_BASE}/issues/sync`, { method: 'POST' }),

    analyze: (id: number): Promise<Analysis> =>
      fetchJson(`${API_BASE}/issues/${id}/analyze`, { method: 'POST' }),

    analyses: (id: number): Promise<Analysis[]> =>
      fetchJson(`${API_BASE}/issues/${id}/analyses`),
  },

  health: (): Promise<{ status: string; service: string; version: string }> =>
    fetchJson('/health'),
};