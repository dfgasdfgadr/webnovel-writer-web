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
  created_at: string;
  updated_at: string;
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
}

export interface ChapterUpdate {
  title?: string;
  content?: string;
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
