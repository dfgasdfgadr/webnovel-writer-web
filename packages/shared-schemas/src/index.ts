// === NovelCraft Shared Schemas ===
// Canonical TypeScript types shared between frontend and backend.
// Frontend imports from here; backend Pydantic models mirror these shapes.

// ─── Auth ───
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  display_name?: string;
}

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

// ─── Project ───
export interface ProjectPublic {
  id: string;
  title: string;
  description: string | null;
  genre: string | null;
  status: string;
  owner_id: string;
  volume_label?: string | null;
  root_dir?: string | null;
  synopsis_json?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SynopsisRequest {
  genre: string;
  hook: string;
  protagonist: Record<string, unknown>;
  world_building: Record<string, unknown>;
  power_system: string;
}

export interface SynopsisResponse {
  title: string;
  genre: string;
  hook: string;
  synopsis: string;
  volumes: Array<{
    num: number;
    title: string;
    summary: string;
    target_chapters: number;
  }>;
}

export interface OutlineRequest {
  volume: Record<string, unknown>;
  chapter_num: number;
  synopsis?: Record<string, unknown>;
}

export interface OutlineResponse {
  chapter_num: number;
  title: string;
  outline: string;
  must_cover_nodes: string[];
  forbidden_zones: string[];
  key_characters: Array<{ name: string; role_in_chapter: string }>;
  target_words: number;
}

export interface BatchOutlineRequest {
  volume: Record<string, unknown>;
  start_chapter: number;
  end_chapter: number;
  synopsis?: Record<string, unknown>;
}

export interface BatchOutlineResponse {
  total: number;
  completed: number;
  failed: number;
  results: Array<{
    chapter_num: number;
    success: boolean;
    data?: OutlineResponse;
    error?: string;
  }>;
}

export interface VolumePlanRequest {
  synopsis: Record<string, unknown>;
  total_chapters: number;
  chapters_per_volume: number;
}

export interface VolumePlanResponse {
  total_volumes: number;
  volumes: Array<{
    num: number;
    title: string;
    summary: string;
    target_chapters: number;
    chapters?: Array<OutlineResponse>;
  }>;
}

export interface ProjectCreate {
  title: string;
  description?: string;
  genre?: string;
}

export interface ProjectUpdate {
  title?: string;
  description?: string;
  genre?: string;
  status?: string;
  volume_label?: string | null;
}

export interface ProjectList {
  items: ProjectPublic[];
  total: number;
}

// ─── Chapter ───
export interface ChapterPublic {
  id: string;
  project_id: string;
  title: string;
  number: number;
  content: string;
  outline: string;
  word_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ChapterCreate {
  project_id: string;
  title: string;
  number: number;
  content?: string;
  outline?: string;
}

export interface ChapterUpdate {
  title?: string;
  content?: string;
  outline?: string;
  status?: string;
}

export interface ChapterList {
  items: ChapterPublic[];
  total: number;
}

// ─── Agents ───
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

export interface PipelineStatus {
  success: boolean;
  step_results: { step: string; result: Record<string, unknown> }[];
  blocking_issues: ReviewIssue[];
  chapter_text: string;
  error: string | null;
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

// ─── LLM Settings ───
export interface LlmSettingsResponse {
  id: string;
  user_id: string;
  api_key_masked: string | null;
  base_url: string | null;
  model: string | null;
  created_at: string;
  updated_at: string;
}

export interface LlmSettingsRequest {
  api_key?: string | null;
  base_url?: string | null;
  model?: string | null;
}

export interface ConnectionTestResponse {
  success: boolean;
  message: string;
  elapsed_ms: number;
}

// ─── Graph & Continuity ───
export interface GraphNode {
  id: string;
  name: string;
  type: string;
  description: string | null;
  importance: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  description: string | null;
}

export interface TimelineItem {
  id: string;
  title: string;
  status: string;
  chapter_planted: number | null;
  chapter_resolved: number | null;
  description: string | null;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  timeline: TimelineItem[];
}

// ─── Simulation ───
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

// ─── Disambiguation ───
export type DisambiguationStatus = "pending" | "accepted" | "rejected";

export interface DisambiguationItemPublic {
  id: string;
  project_id: string;
  chapter_id: string | null;
  field_name: string;
  current_value: string;
  confidence: number;
  alternatives: string;
  suggestion: string | null;
  status: DisambiguationStatus;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface DisambiguationResolveRequest {
  status: "accepted" | "rejected";
  resolved_by: string;
}

export interface DisambiguationListResponse {
  items: DisambiguationItemPublic[];
  total: number;
}

// ─── Summary ───
export type SummaryLevel = "volume" | "arc" | "chapter";

export interface SummaryPublic {
  id: string;
  project_id: string;
  level: SummaryLevel;
  scope_label: string;
  parent_id: string | null;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface SummaryCreateRequest {
  level: SummaryLevel;
  scope_label: string;
  parent_id?: string | null;
  title: string;
  content: string;
}

export interface SummaryUpdateRequest {
  title?: string;
  content?: string;
}

// ─── Review Metrics ───
export interface ReviewMetricPublic {
  id: string;
  chapter_id: string;
  project_id: string;
  consistency_score: number;
  timeline_score: number;
  coherence_score: number;
  ooc_score: number;
  logic_score: number;
  foreshadowing_score: number;
  ai_flavor_score: number;
  summary: string | null;
  created_at: string;
}

// ─── Polish ───
export interface PolishAxesResponse {
  axes: Record<string, string>;
}

export interface PolishRequest {
  issues: Array<Record<string, unknown>>;
  enabled_axes?: string[] | null;
  chapter_outline?: string;
}

export interface PolishResponse {
  result: {
    summary?: string;
    diff?: Array<{ before: string; after: string; axis: string }>;
    raw?: string;
  };
  token_input: number;
  token_output: number;
}

// ─── API Wrappers ───
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
