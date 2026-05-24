const BASE_URL = "/api/v1";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data as T;
}

// ---- Auth ----
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserPublic {
  id: string;
  username: string;
  display_name: string | null;
  created_at: string;
}

export function login(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.set("username", username);
  formData.set("password", password);
  return fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  }).then(async (res) => {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    return data as TokenResponse;
  });
}

export function register(username: string, password: string, displayName?: string) {
  return request<UserPublic>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, display_name: displayName }),
  });
}

export function getMe() {
  return request<UserPublic>("/auth/me");
}

// ---- Projects ----
export interface ProjectPublic {
  id: string;
  title: string;
  description: string | null;
  genre: string | null;
  status: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectList {
  items: ProjectPublic[];
  total: number;
}

export function listProjects() {
  return request<ProjectList>("/projects");
}

export function createProject(data: { title: string; description?: string; genre?: string }) {
  return request<ProjectPublic>("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getProject(id: string) {
  return request<ProjectPublic>(`/projects/${id}`);
}

export function updateProject(id: string, data: Record<string, unknown>) {
  return request<ProjectPublic>(`/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteProject(id: string) {
  return request<void>(`/projects/${id}`, { method: "DELETE" });
}

// ---- Chapters ----
export interface ChapterPublic {
  id: string;
  project_id: string;
  title: string;
  number: number;
  content: string;
  word_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ChapterList {
  items: ChapterPublic[];
  total: number;
}

export function listChapters(projectId: string) {
  return request<ChapterList>(`/projects/${projectId}/chapters`);
}

export function createChapter(projectId: string, data: { title: string; number: number; content?: string }) {
  return request<ChapterPublic>(`/projects/${projectId}/chapters`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getChapter(projectId: string, chapterId: string) {
  return request<ChapterPublic>(`/projects/${projectId}/chapters/${chapterId}`);
}

export function updateChapter(projectId: string, chapterId: string, data: { title?: string; content?: string; status?: string }) {
  return request<ChapterPublic>(`/projects/${projectId}/chapters/${chapterId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteChapter(projectId: string, chapterId: string) {
  return request<void>(`/projects/${projectId}/chapters/${chapterId}`, { method: "DELETE" });
}

// ---- Agents ----
export interface PipelineStatus {
  success: boolean;
  step_results: { step: string; result: Record<string, unknown> }[];
  blocking_issues: ReviewIssue[];
  chapter_text: string;
  error: string | null;
}

export interface ReviewIssue {
  id: string;
  severity: "blocking" | "major" | "minor";
  category: string;
  title: string;
  description: string;
  evidence: string;
  suggestion: string | null;
  is_fixed: boolean;
  created_at: string;
}

export interface AgentRunPublic {
  id: string;
  agent_type: string;
  phase: string;
  status: string;
  token_input: number;
  token_output: number;
  elapsed_ms: number;
  error_message: string | null;
  created_at: string;
}

export function runPipeline(chapterId: string, outline: string) {
  return request<PipelineStatus>(`/agents/pipeline/${chapterId}`, {
    method: "POST",
    body: JSON.stringify({ chapter_outline: outline }),
  });
}

export function streamDraftUrl(chapterId: string, outline: string): string {
  const token = getToken();
  const params = new URLSearchParams({ outline, token: token || "" });
  return `${BASE_URL}/agents/pipeline/${chapterId}/stream?${params.toString()}`;
}

export function getReviews(chapterId: string) {
  return request<ReviewIssue[]>(`/agents/reviews/${chapterId}`);
}

export function listAgentRuns(projectId: string) {
  return request<AgentRunPublic[]>(`/agents/runs/${projectId}`);
}
