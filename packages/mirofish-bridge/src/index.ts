/**
 * MiroFish Bridge — seed packet assembly and HTTP client for MiroFish Sidecar.
 *
 * Gracefully degrades when MiroFish is unavailable (no Docker / not running).
 */

// ---- Types ----

export interface SeedPacket {
  /** Project ID for tracking */
  project_id: string;
  /** Simulation brief — natural language description of what to simulate */
  sim_brief: string;
  /** Simulation mode */
  mode: "pre_chapter" | "branch_explore";
  /** Project context (setting, characters, world rules) */
  context: {
    master_setting?: Record<string, unknown>;
    characters?: Array<{ name: string; info: Record<string, unknown> }>;
    world_rules?: string[];
  };
  /** Chapters to include as reference */
  chapter_texts: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  /** For branch_explore: snapshot before branching point */
  pre_branch_state?: Record<string, unknown>;
  /** Optional parameters */
  options?: {
    max_sim_steps?: number;
    temperature?: number;
    checkpoint_id?: string;
  };
}

export interface SimStep {
  step: string;
  status: "pending" | "running" | "completed" | "failed";
  description: string;
  data?: Record<string, unknown>;
}

export interface SimReport {
  sim_id: string;
  mode: string;
  status: "running" | "completed" | "failed";
  steps: SimStep[];
  /** Structured report output */
  events?: Array<{ probability: number; description: string; impact: string }>;
  risks?: Array<{ risk: string; severity: string; mitigation: string }>;
  suggestions?: Array<{ type: string; target: string; action: string; reason: string }>;
  checkpoint_id?: string;
  error?: string;
}

export interface SimStatus {
  sim_id: string;
  status: string;
  progress: number; // 0-100
  current_step: string;
}

// ---- Seed Packet Assembly ----

export function assembleSeedPacket(params: {
  project_id: string;
  sim_brief: string;
  mode: "pre_chapter" | "branch_explore";
  context?: SeedPacket["context"];
  chapter_texts?: SeedPacket["chapter_texts"];
  pre_branch_state?: Record<string, unknown>;
  checkpoint_id?: string;
}): SeedPacket {
  return {
    project_id: params.project_id,
    sim_brief: params.sim_brief,
    mode: params.mode,
    context: params.context || { characters: [], world_rules: [] },
    chapter_texts: params.chapter_texts || [],
    pre_branch_state: params.pre_branch_state,
    options: {
      max_sim_steps: 10,
      temperature: 0.7,
      checkpoint_id: params.checkpoint_id,
    },
  };
}

// ---- HTTP Client ----

const DEFAULT_MIROFISH_URL = "http://localhost:8081";

export class MiroFishClient {
  private baseUrl: string;
  private available: boolean | null = null;

  constructor(baseUrl: string = DEFAULT_MIROFISH_URL) {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const resp = await fetch(`${this.baseUrl}/health`, {
        signal: AbortSignal.timeout(3000),
      });
      this.available = resp.ok;
      return resp.ok;
    } catch {
      this.available = false;
      return false;
    }
  }

  isAvailable(): boolean | null {
    return this.available;
  }

  async createSimulation(packet: SeedPacket): Promise<SimReport | null> {
    if (!(await this.checkHealth())) {
      return null; // graceful degradation
    }
    try {
      const resp = await fetch(`${this.baseUrl}/api/v1/simulations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(packet),
        signal: AbortSignal.timeout(60000),
      });
      if (!resp.ok) return null;
      return await resp.json() as SimReport;
    } catch {
      return null;
    }
  }

  async getSimulationStatus(simId: string): Promise<SimStatus | null> {
    if (!(await this.checkHealth())) return null;
    try {
      const resp = await fetch(`${this.baseUrl}/api/v1/simulations/${simId}/status`, {
        signal: AbortSignal.timeout(5000),
      });
      if (!resp.ok) return null;
      return await resp.json() as SimStatus;
    } catch {
      return null;
    }
  }

  async getSimulationReport(simId: string): Promise<SimReport | null> {
    if (!(await this.checkHealth())) return null;
    try {
      const resp = await fetch(`${this.baseUrl}/api/v1/simulations/${simId}`, {
        signal: AbortSignal.timeout(30000),
      });
      if (!resp.ok) return null;
      return await resp.json() as SimReport;
    } catch {
      return null;
    }
  }
}

/** Shared singleton for convenience */
export const mirofishClient = new MiroFishClient();
