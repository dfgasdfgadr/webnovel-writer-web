import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as api from "@/lib/api";
import { PlanningCenter } from "./PlanningCenter";

vi.mock("@/lib/api", () => ({
  getProject: vi.fn(),
  generateSynopsis: vi.fn(),
  generateOutline: vi.fn(),
  generateBatchOutlines: vi.fn(),
  generateVolumePlan: vi.fn(),
}));

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/proj-1/planning"]}>
        <PlanningCenter />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockProject = {
  id: "proj-1",
  title: "测试项目",
  description: null,
  genre: null,
  status: "active",
  owner_id: "user-1",
  synopsis_json: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("PlanningCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
  });

  afterEach(() => {
    cleanup();
  });

  it("shows loading skeleton initially", () => {
    vi.mocked(api.getProject).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByRole("heading", { name: "规划中心" })).toBeInTheDocument();
  });

  it("renders page with project title", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("测试项目")).toBeInTheDocument();
    });
    expect(screen.getByText("规划中心 (WIP)")).toBeInTheDocument();
  });

  it("shows ProjectNav with planning tab active", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("规划中心")).toBeInTheDocument();
    });
    const navLink = screen.getByText("规划中心");
    expect(navLink.getAttribute("aria-current")).toBe("page");
  });
});
