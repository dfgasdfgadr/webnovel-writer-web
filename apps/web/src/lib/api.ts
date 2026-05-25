import type {
  TokenResponse,
  UserPublic,
  ProjectPublic,
  ProjectList,
  ChapterPublic,
  ChapterList,
  ReviewIssue,
  PipelineStatus,
  AgentRunPublic,
  LlmSettingsResponse,
  ConnectionTestResponse,
  GraphNode,
  GraphEdge,
  TimelineItem,
  GraphData,
  SynopsisRequest,
  SynopsisResponse,
  OutlineRequest,
  OutlineResponse,
  BatchOutlineRequest,
  BatchOutlineResponse,
  VolumePlanRequest,
  VolumePlanResponse,
  DisambiguationItemPublic,
  DisambiguationListResponse,
  SummaryPublic,
  SummaryCreateRequest,
  SummaryUpdateRequest,
  ReviewMetricPublic,
  PolishAxesResponse,
  PolishRequest,
  PolishResponse,
} from "@novelcraft/shared-schemas";

// Re-export types for consumers
export type {
  TokenResponse,
  UserPublic,
  ProjectPublic,
  ProjectList,
  ChapterPublic,
  ChapterList,
  ReviewIssue,
  PipelineStatus,
  AgentRunPublic,
  LlmSettingsResponse,
  ConnectionTestResponse,
  GraphNode,
  GraphEdge,
  TimelineItem,
  GraphData,
  SynopsisRequest,
  SynopsisResponse,
  OutlineRequest,
  OutlineResponse,
  BatchOutlineRequest,
  BatchOutlineResponse,
  VolumePlanRequest,
  VolumePlanResponse,
  DisambiguationItemPublic,
  DisambiguationListResponse,
  SummaryPublic,
  SummaryCreateRequest,
  SummaryUpdateRequest,
  ReviewMetricPublic,
  PolishAxesResponse,
  PolishRequest,
  PolishResponse,
};

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
export function login(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.set("username", username);
  formData.set("password", password);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  return fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
    signal: controller.signal,
  })
    .then(async (res) => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      return data as TokenResponse;
    })
    .catch((err) => {
      if (err instanceof Error && err.name === "AbortError") {
        throw new Error("登录超时：请确认后端已启动（pnpm dev:api）");
      }
      throw err;
    })
    .finally(() => clearTimeout(timer));
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
export function listProjects() {
  return request<ProjectList>("/projects");
}

export function createProject(data: {
  title: string;
  description?: string;
  genre?: string;
  hook?: string;
  protagonist?: Record<string, unknown>;
  world_building?: Record<string, unknown>;
  power_system?: string;
  golden_finger?: string;
  constraints?: string[];
  target_words?: number;
  target_chapters?: number;
}) {
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

// ---- Import ----
export interface ImportScanResult {
  valid: boolean;
  source_path: string;
  title: string;
  errors: string[];
  chapter_count: number;
  settings_count: number;
  has_synopsis: boolean;
  has_story_system: boolean;
  has_webnovel: boolean;
  chapters_preview: Array<{ number: number; title: string; word_count: number }>;
  settings_preview: string[];
}

export function scanImport(sourcePath: string) {
  return request<ImportScanResult>("/projects/import/scan", {
    method: "POST",
    body: JSON.stringify({ source_path: sourcePath }),
  });
}

export function executeImport(sourcePath: string, title?: string) {
  return request<ProjectPublic>("/projects/import", {
    method: "POST",
    body: JSON.stringify({ source_path: sourcePath, title }),
  });
}

// ---- Chapters ----
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

export function updateChapter(
  projectId: string,
  chapterId: string,
  data: { title?: string; content?: string; outline?: string; status?: string }
) {
  return request<ChapterPublic>(`/projects/${projectId}/chapters/${chapterId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteChapter(projectId: string, chapterId: string) {
  return request<void>(`/projects/${projectId}/chapters/${chapterId}`, { method: "DELETE" });
}

// ---- Agents ----
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

export function runReview(chapterId: string, data?: { content?: string; outline?: string }) {
  return request<ReviewIssue[]>(`/agents/reviews/${chapterId}/run`, {
    method: "POST",
    body: JSON.stringify(data ?? {}),
  });
}

export function listAgentRuns(projectId: string) {
  return request<AgentRunPublic[]>(`/agents/runs/${projectId}`);
}

// ---- Settings ----
export function getLlmSettings() {
  return request<LlmSettingsResponse>("/settings/llm");
}

export function updateLlmSettings(data: { api_key?: string; base_url?: string; model?: string }) {
  return request<LlmSettingsResponse>("/settings/llm", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function testLlmConnection(data?: { api_key?: string; base_url?: string; model?: string }) {
  return request<ConnectionTestResponse>("/settings/llm/test", {
    method: "POST",
    body: JSON.stringify(data || {}),
  });
}

// ---- Graph & Continuity ----
export function getGraphData(projectId: string) {
  return request<GraphData>(`/agents/graph/${projectId}`);
}

// ---- Architect (Planning Center) ----
export function generateSynopsis(projectId: string, data: SynopsisRequest) {
  return request<SynopsisResponse>(`/agents/architect/synopsis/${projectId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function generateOutline(projectId: string, data: OutlineRequest) {
  return request<OutlineResponse>(`/agents/architect/outline/${projectId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function generateBatchOutlines(projectId: string, data: BatchOutlineRequest) {
  return request<BatchOutlineResponse>(`/agents/architect/outline/${projectId}/batch`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function generateVolumePlan(projectId: string, data: VolumePlanRequest) {
  return request<VolumePlanResponse>(`/agents/architect/volume-plan/${projectId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---- Checkpoint ----
export interface CheckpointData {
  phase: string;
  flow: string;
  step: string;
  chapter_id: string;
  project_id: string;
  payload?: Record<string, unknown>;
}

export function getCheckpoint(chapterId: string) {
  return request<{ checkpoint: CheckpointData | null }>(`/agents/pipeline/${chapterId}/checkpoint`);
}

export function resumeCheckpoint(chapterId: string, step: string) {
  return request<PipelineStatus>(`/agents/pipeline/${chapterId}/checkpoint/resume`, {
    method: "POST",
    body: JSON.stringify({ step }),
  });
}

// ---- Polish ----
export function getPolishAxes() {
  return request<PolishAxesResponse>("/agents/polish/axes");
}

export function polishChapter(chapterId: string, data: PolishRequest) {
  return request<PolishResponse>(`/agents/polish/${chapterId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function streamPolishUrl(chapterId: string): string {
  const token = getToken();
  const params = new URLSearchParams({ token: token || "" });
  return `${BASE_URL}/agents/polish/${chapterId}/stream?${params.toString()}`;
}

// ---- Review Metrics ----
export function getReviewMetrics(chapterId: string) {
  return request<ReviewMetricPublic[]>(`/agents/reviews/${chapterId}/metrics`);
}

// ---- Disambiguation ----
export function listDisambiguationItems(projectId: string, status?: string) {
  const params = status ? `?status=${status}` : "";
  return request<DisambiguationListResponse>(`/disambiguation/${projectId}${params}`);
}

export function resolveDisambiguationItem(projectId: string, itemId: string, data: { status: string; resolved_by: string }) {
  return request<DisambiguationItemPublic>(`/disambiguation/${projectId}/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ---- Summaries ----
export function listSummaries(projectId: string, level?: string) {
  const params = level ? `?level=${level}` : "";
  return request<SummaryPublic[]>(`/summaries/${projectId}${params}`);
}

export function createSummary(projectId: string, data: SummaryCreateRequest) {
  return request<SummaryPublic>(`/summaries/${projectId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateSummary(projectId: string, summaryId: string, data: SummaryUpdateRequest) {
  return request<SummaryPublic>(`/summaries/${projectId}/${summaryId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteSummary(projectId: string, summaryId: string) {
  return request<void>(`/summaries/${projectId}/${summaryId}`, { method: "DELETE" });
}
