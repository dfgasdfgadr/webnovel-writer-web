import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  getProject: vi.fn(),
  getGraphData: vi.fn(),
  request: vi.fn(),
}));

import * as api from "@/lib/api";
import { GraphView } from "./GraphView";

function renderPage(projectId = "p1") {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/graph`]}>
        <Routes>
          <Route path="/projects/:projectId/graph" element={<GraphView />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("GraphView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton initially", () => {
    vi.mocked(api.getProject).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getGraphData).mockReturnValue(new Promise(() => {}));
    renderPage();
    const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders empty state when no data", async () => {
    vi.mocked(api.getProject).mockResolvedValue({
      id: "p1", title: "测试项目", description: null,
      genre: null, status: "active", owner_id: "u1",
      created_at: "", updated_at: "",
    });
    vi.mocked(api.getGraphData).mockResolvedValue({
      nodes: [], edges: [], timeline: [],
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("暂无实体数据")).toBeInTheDocument();
    });
  });

  it("renders title when graph has nodes", async () => {
    vi.mocked(api.getProject).mockResolvedValue({
      id: "p1", title: "测试项目", description: null,
      genre: null, status: "active", owner_id: "u1",
      created_at: "", updated_at: "",
    });
    vi.mocked(api.getGraphData).mockResolvedValue({
      nodes: [
        { id: "n1", name: "主角", type: "character", description: "修炼者", importance: 5 },
        { id: "n2", name: "反派", type: "character", description: "魔教教主", importance: 4 },
      ],
      edges: [
        { id: "e1", source: "n1", target: "n2", label: "敌对", description: null },
      ],
      timeline: [],
    });

    renderPage();

    await waitFor(() => {
      const titles = screen.getAllByText("关系图谱");
      expect(titles.length).toBeGreaterThan(0);
    });
  });

  it("shows tabs for graph and timeline", async () => {
    vi.mocked(api.getProject).mockResolvedValue({
      id: "p1", title: "测试项目", description: null,
      genre: null, status: "active", owner_id: "u1",
      created_at: "", updated_at: "",
    });
    vi.mocked(api.getGraphData).mockResolvedValue({
      nodes: [],
      edges: [],
      timeline: [
        { id: "f1", title: "伏笔A", status: "planted", chapter_planted: 5, chapter_resolved: null, description: null },
      ],
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("实体关系图")).toBeInTheDocument();
    });
    expect(screen.getByText("伏笔时间线")).toBeInTheDocument();
  });
});
