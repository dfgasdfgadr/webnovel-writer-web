// === NovelCraft Shared Schemas ===
// Phase 0: core API types shared between frontend and backend

// --------------- Auth ---------------
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
  token_type: "bearer";
}

export interface UserPublic {
  id: string;
  username: string;
  display_name: string | null;
  created_at: string;
}

// --------------- Project ---------------
export type ProjectStatus = "active" | "archived";

export interface ProjectCreate {
  title: string;
  description?: string;
  genre?: string;
}

export interface ProjectUpdate {
  title?: string;
  description?: string;
  genre?: string;
  status?: ProjectStatus;
}

export interface ProjectPublic {
  id: string;
  title: string;
  description: string | null;
  genre: string | null;
  status: ProjectStatus;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

// --------------- Chapter ---------------
export type ChapterStatus = "draft" | "reviewing" | "accepted" | "archived";

export interface ChapterCreate {
  project_id: string;
  title: string;
  number: number;
  content?: string;
}

export interface ChapterUpdate {
  title?: string;
  content?: string;
  status?: ChapterStatus;
}

export interface ChapterPublic {
  id: string;
  project_id: string;
  title: string;
  number: number;
  content: string;
  word_count: number;
  status: ChapterStatus;
  created_at: string;
  updated_at: string;
}

// --------------- API Wrappers ---------------
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
