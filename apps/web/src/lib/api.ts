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
  CardPublic,
  CardCreate,
  EntityPublic,
  EntityCreate,
  EntityUpdate,
  RelationshipPublic,
  RelationshipCreate,
  ReferenceCorpusPublic,
  ReferenceCorpusDetail,
  ReferenceCorpusList,
  ReferenceSearchResult,
  ReferenceSearchResponse,
  DeconstructionRunPublic,
  DeconstructionRunStartResponse,
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
  CardPublic,
  CardCreate,
  EntityPublic,
  EntityCreate,
  EntityUpdate,
  RelationshipPublic,
  RelationshipCreate,
  ReferenceCorpusPublic,
  ReferenceCorpusDetail,
  ReferenceCorpusList,
  ReferenceSearchResult,
  ReferenceSearchResponse,
  DeconstructionRunPublic,
  DeconstructionRunStartResponse,
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

export function exportProjectUrl(projectId: string): string {
  const token = getToken();
  return `${BASE_URL}/projects/${projectId}/export?token=${token || ""}`;
}

export function executeImport(sourcePath: string, title?: string) {
  return request<ProjectPublic>("/projects/import", {
    method: "POST",
    body: JSON.stringify({ source_path: sourcePath, title }),
  });
}

export async function importZip(file: File): Promise<ProjectPublic> {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/projects/import/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Import failed");
  return data as ProjectPublic;
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

export function generateSummary(projectId: string, data: { level: string; scope_label?: string; chapter_ids?: string[]; parent_id?: string }) {
  return request<SummaryPublic & { key_events: string[]; character_arcs: string[]; cliffhangers: string[] }>(
    `/summaries/${projectId}/generate`,
    { method: "POST", body: JSON.stringify(data) }
  );
}

// ---- Cards ----
export function listCards(projectId: string, cardType?: string) {
  const params = cardType ? `?card_type=${cardType}` : "";
  return request<CardPublic[]>(`/projects/${projectId}/cards${params}`);
}

export function createCard(projectId: string, data: CardCreate) {
  return request<CardPublic>(`/projects/${projectId}/cards`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteCard(projectId: string, cardId: string) {
  return request<void>(`/projects/${projectId}/cards/${cardId}`, { method: "DELETE" });
}

// ---- Entities ----
export function listEntities(projectId: string, entityType?: string) {
  const params = entityType ? `?entity_type=${entityType}` : "";
  return request<EntityPublic[]>(`/projects/${projectId}/entities${params}`);
}

export function createEntity(projectId: string, data: EntityCreate) {
  return request<EntityPublic>(`/projects/${projectId}/entities`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateEntity(projectId: string, entityId: string, data: EntityUpdate) {
  return request<{ ok: boolean }>(`/projects/${projectId}/entities/${entityId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteEntity(projectId: string, entityId: string) {
  return request<void>(`/projects/${projectId}/entities/${entityId}`, { method: "DELETE" });
}

// ---- Relationships ----
export function listRelationships(projectId: string) {
  return request<RelationshipPublic[]>(`/projects/${projectId}/relationships`);
}

export function createRelationship(projectId: string, data: RelationshipCreate) {
  return request<RelationshipPublic>(`/projects/${projectId}/relationships`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---- Search ----
export interface SearchResult {
  doc_id: string;
  title: string;
  content: string;
  score: number;
  meta: Record<string, unknown>;
}

export function searchProject(projectId: string, q: string, filter?: string) {
  const params = new URLSearchParams({ q });
  if (filter) params.set("filter", filter);
  return request<SearchResult[]>(`/agents/search/${projectId}?${params.toString()}`);
}

// ---- Plugins ----
export interface PluginInfo {
  name: string;
  display_name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  triggers: string[];
  loaded: boolean;
}

export function listPlugins() {
  return request<{ plugins: PluginInfo[]; total: number }>("/plugins");
}

export function togglePlugin(name: string, enabled: boolean) {
  return request<{ name: string; enabled: boolean }>(`/plugins/${name}/toggle`, {
    method: "POST",
    body: JSON.stringify({ enabled }),
  });
}

export function loadPlugin(name: string) {
  return request<{ name: string; loaded: boolean }>(`/plugins/${name}/load`, {
    method: "POST",
  });
}

export function reloadPlugins() {
  return request<{ discovered: number; plugins: PluginInfo[] }>("/plugins/reload", {
    method: "POST",
  });
}

// ---- Workflows ----
export interface WorkflowAction {
  name: string;
  type: string;
  config: Record<string, unknown>;
}

export interface WorkflowRule {
  name: string;
  trigger: string;
  enabled: boolean;
  actions: WorkflowAction[];
  condition: Record<string, unknown>;
}

export function listWorkflows() {
  return request<{ rules: WorkflowRule[]; total: number; builtin_count: number }>("/plugins/workflows");
}

export function toggleWorkflowRule(name: string, enabled: boolean) {
  return request<{ name: string; enabled: boolean }>(
    `/plugins/workflows/${encodeURIComponent(name)}/toggle?enabled=${enabled}`,
    { method: "POST" },
  );
}

// ---- Simulations ----
export interface SimJob {
  id: string;
  project_id: string;
  mode: string;
  status: string;
  progress: number;
  mirofish_available: boolean;
  report: Record<string, unknown> | null;
  steps: Array<{ step: string; status: string; description: string }> | null;
  error_message: string | null;
  created_at: string;
}

export function listSimulations(projectId: string) {
  return request<SimJob[]>(`/simulations?project_id=${projectId}`);
}

export function getSimulation(id: string) {
  return request<SimJob>(`/simulations/${id}`);
}

export function createSimulation(data: { project_id: string; mode: string; sim_brief: string }) {
  return request<SimJob>("/simulations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function adoptSimulation(simId: string) {
  return request<{ success: boolean }>(`/simulations/${simId}/adopt`, {
    method: "POST",
  });
}

// ---- InitChat SSE ----
export interface InitChatMessage {
  role: string;
  content: string;
}

export interface InitScheme {
  name: string;
  genre_focus: string;
  hook_variation: string;
  power_evolution: string;
  target_scale: string;
  scores: {
    innovation: number;
    marketability: number;
    coherence: number;
    depth: number;
    readability: number;
  };
}

export interface InitChatResponse {
  status: "asking" | "complete" | "confirmed" | "error";
  missing_fields?: string[];
  question?: string;
  hint?: string;
  schemes?: InitScheme[];
  error?: string;
}

/** POST-based SSE stream for InitChat. Parses `data: {...}\n\n` lines. */
export async function* initChatStream(
  message: string,
  history: InitChatMessage[]
): AsyncGenerator<InitChatResponse, void, unknown> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}/projects/init/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, history }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Init chat failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        const payload = trimmed.slice(6);
        if (payload === "[DONE]") return;
        try {
          yield JSON.parse(payload) as InitChatResponse;
        } catch {
          // ignore unparseable lines
        }
      }
    }
  }
}

export function initSchemes(premise: Record<string, unknown>) {
  return request<{ status: string; schemes?: InitScheme[]; error?: string }>("/projects/init/schemes", {
    method: "POST",
    body: JSON.stringify({ premise }),
  });
}

// ---- Deconstruct SSE ----
export interface DeconstructResponse {
  status: "analyzing" | "done" | "error";
  message?: string;
  deconstruction?: {
    golden_chapters?: string[];
    hooks?: string[];
    character_patterns?: string[];
    world_patterns?: string[];
    pacing?: string[];
    transferable_patterns?: string[];
    red_flags?: string[];
  };
  warning?: string;
  error?: string;
}

/** POST-based SSE stream for Deconstruct. */
export async function* deconstructStream(
  bookTitle: string,
  sampleChapters: string[]
): AsyncGenerator<DeconstructResponse, void, unknown> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}/projects/init/deconstruct/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ book_title: bookTitle, sample_chapters: sampleChapters }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Deconstruct failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        const payload = trimmed.slice(6);
        if (payload === "[DONE]") return;
        try {
          yield JSON.parse(payload) as DeconstructResponse;
        } catch {
          // ignore unparseable lines
        }
      }
    }
  }
}

// ---- Backup & Workflow History ----
export interface BackupStatus {
  enabled: boolean;
  status: string;
  last_run: string | null;
  chapter_num?: string;
  reason?: string;
  total_runs?: number;
}

export function getBackupStatus(projectId: string) {
  return request<BackupStatus>(`/projects/${projectId}/backup-status`);
}

export interface WorkflowRun {
  timestamp: string;
  trigger: string;
  action: string;
  status: string;
  chapter_num?: string;
  reason?: string;
}

export function getWorkflowHistory(projectId: string, limit?: number) {
  const params = limit ? `?limit=${limit}` : "";
  return request<{ runs: WorkflowRun[]; total: number }>(`/projects/${projectId}/workflow-history${params}`);
}

// ---- Reader Pulse ----
export interface ReaderPulsePublic {
  id: string;
  chapter_id: string;
  project_id: string;
  drop_risk: number;
  hook_quality: number;
  pacing_score: number;
  expectation: string;
  strengths: string[];
  weaknesses: string[];
  next_chapter_suggestion: string;
  overall_verdict: string;
  created_at: string;
}

export function getReaderPulse(chapterId: string) {
  return request<ReaderPulsePublic[]>(`/agents/reader-pulse/${chapterId}`);
}

export function runReaderPulse(chapterId: string) {
  return request<ReaderPulsePublic>(`/agents/reader-pulse/${chapterId}`, {
    method: "POST",
  });
}

// ---- Prompt Workshop ----
export interface PromptEntry {
  scope: string;
  key: string;
  content: string;
  is_default: boolean;
}

export function getProjectPrompts(projectId: string, scope?: string) {
  const params = scope ? `?scope=${scope}` : "";
  return request<{ prompts: PromptEntry[] }>(`/projects/${projectId}/prompts${params}`);
}

export function updateProjectPrompt(projectId: string, scope: string, key: string, content: string) {
  return request<{ scope: string; key: string; content: string }>(
    `/projects/${projectId}/prompts/${scope}/${key}`,
    { method: "PUT", body: JSON.stringify({ content }) },
  );
}

export function resetProjectPrompt(projectId: string, scope: string, key: string) {
  return request<{ scope: string; key: string; content: string; reset: boolean }>(
    `/projects/${projectId}/prompts/${scope}/${key}/reset`,
    { method: "POST" },
  );
}

// ---- Story Foundry ----

export interface FoundryDeconstruction {
  golden_chapters: string[];
  hooks: string[];
  character_patterns: string[];
  world_patterns: string[];
  pacing: string[];
  transferable_patterns: string[];
  red_flags: string[];
}

export interface FoundryChapterGroup {
  label: string;
  content: string;
}

export interface FoundryDeconstructRequest {
  book_title: string;
  sample_chapters: string[];
  mode?: "quick" | "representative" | "fullbook";
  chapter_groups?: FoundryChapterGroup[];
}

export interface FoundryDeconstructResponse {
  status: string;
  deconstruction: FoundryDeconstruction;
  fallback: boolean;
}

export interface QuestionOption {
  id: string;
  label: string;
  description: string;
  effects: {
    protagonist?: Record<string, unknown>;
    plot_bias?: Record<string, unknown>;
    pacing?: Record<string, unknown>;
  };
}

export interface QuestionSet {
  id: string;
  title: string;
  description: string;
  options: QuestionOption[];
}

export interface FoundryQuestionsRequest {
  deconstruction: FoundryDeconstruction;
  preferences?: Record<string, unknown>;
}

export interface FoundryQuestionsResponse {
  question_sets: QuestionSet[];
  fallback: boolean;
}

export interface FoundryComposeRequest {
  book_title: string;
  deconstruction: FoundryDeconstruction;
  selections: Record<string, string>;
  custom_notes?: string;
}

export interface FoundryComposeResponse {
  premise: Record<string, unknown>;
  master_setting: Record<string, unknown>;
  synopsis: Record<string, unknown>;
  first_volume_chapters: Array<{
    chapter_num: number;
    title: string;
    outline: string;
    must_cover_nodes: string[];
    forbidden_zones: string[];
    key_characters: Array<{ name: string; role_in_chapter: string }>;
    target_words: number;
  }>;
  fallback: boolean;
}

export function foundryDeconstruct(data: FoundryDeconstructRequest) {
  return request<FoundryDeconstructResponse>("/agents/foundry/deconstruct", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function foundryQuestions(data: FoundryQuestionsRequest) {
  return request<FoundryQuestionsResponse>("/agents/foundry/questions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function foundryCompose(data: FoundryComposeRequest) {
  return request<FoundryComposeResponse>("/agents/foundry/compose", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---- Full-book Deconstruction ----

export function startFullBookDeconstruct(
  corpusId: string,
  targetGenre?: string,
  preferences?: Record<string, unknown>,
) {
  return request<DeconstructionRunStartResponse>(
    "/agents/foundry/deconstruct/fullbook",
    {
      method: "POST",
      body: JSON.stringify({
        corpus_id: corpusId,
        target_genre: targetGenre || "",
        preferences: preferences || {},
        use_embedding: false,
      }),
    },
  );
}

export function getDeconstructionRun(runId: string) {
  return request<DeconstructionRunPublic>(
    `/agents/foundry/deconstruct-runs/${runId}`,
  );
}

// ---- Reference Corpus ----

export function listReferenceCorpora() {
  return request<ReferenceCorpusList>("/reference-corpora");
}

export function createReferenceCorpus(data: {
  title: string;
  author?: string;
  description?: string;
  content: string;
}) {
  return request<ReferenceCorpusPublic>("/reference-corpora", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function uploadReferenceCorpus(
  file: File,
  title?: string,
  author?: string,
  description?: string,
) {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);
  if (title) formData.append("title", title);
  if (author) formData.append("author", author);
  if (description) formData.append("description", description);

  return fetch(`${BASE_URL}/reference-corpora/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  }).then(async (res) => {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    return data as ReferenceCorpusPublic;
  });
}

export function getReferenceCorpus(corpusId: string) {
  return request<ReferenceCorpusDetail>(`/reference-corpora/${corpusId}`);
}

export function deleteReferenceCorpus(corpusId: string) {
  return request<void>(`/reference-corpora/${corpusId}`, { method: "DELETE" });
}

export function searchReferenceCorpus(
  corpusId: string,
  query: string,
  topK: number = 10,
) {
  return request<ReferenceSearchResponse>(
    `/reference-corpora/${corpusId}/search`,
    {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    },
  );
}
