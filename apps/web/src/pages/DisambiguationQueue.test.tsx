import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as api from "@/lib/api";
import { DisambiguationQueue } from "./DisambiguationQueue";

vi.mock("@/lib/api", () => ({
  getProject: vi.fn(),
  listDisambiguationItems: vi.fn(),
  resolveDisambiguationItem: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/proj-1/disambiguation"]}>
        <Routes>
          <Route path="/projects/:projectId/disambiguation" element={<DisambiguationQueue />} />
        </Routes>
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
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockItems = {
  items: [
    {
      id: "di-1",
      project_id: "proj-1",
      chapter_id: "ch-1",
      field_name: "角色名",
      current_value: "张叁",
      confidence: 0.4,
      alternatives: '["张三", "张山"]',
      suggestion: "可能是'张三'，请确认",
      status: "pending",
      resolved_by: null,
      resolved_at: null,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "di-2",
      project_id: "proj-1",
      chapter_id: "ch-1",
      field_name: "功法名称",
      current_value: "星辰诀",
      confidence: 0.85,
      alternatives: '["星辰变", "星辰功"]',
      suggestion: null,
      status: "accepted",
      resolved_by: "user",
      resolved_at: "2026-01-01T00:00:00Z",
      created_at: "2026-01-01T00:00:00Z",
    },
  ],
  total: 2,
};

describe("DisambiguationQueue", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listDisambiguationItems).mockResolvedValue(mockItems);
  });

  afterEach(() => {
    cleanup();
  });

  it("renders page header", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "消歧队列" })).toBeInTheDocument();
    });
  });

  it("shows project title after load", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("测试项目")).toBeInTheDocument();
    });
  });

  it("has filter tabs", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());
    const pendingTabs = screen.getAllByText("待处理");
    expect(pendingTabs.length).toBeGreaterThanOrEqual(1);
    const acceptedTabs = screen.getAllByText("已采纳");
    expect(acceptedTabs.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("已驳回")).toBeInTheDocument();
    expect(screen.getByText("全部")).toBeInTheDocument();
  });

  it("displays items with field_name and confidence", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("角色名")).toBeInTheDocument();
    });
    expect(screen.getByText("功法名称")).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("shows alternatives as badges", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("张三")).toBeInTheDocument();
    });
  });

  it("shows suggestion when present", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/可能是'张三'/)).toBeInTheDocument();
    });
  });

  it("calls resolveDisambiguationItem on accept", async () => {
    vi.mocked(api.resolveDisambiguationItem).mockResolvedValue({ ...mockItems.items[0], status: "accepted" } as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("角色名")).toBeInTheDocument());

    const acceptBtn = screen.getByText("采纳");
    fireEvent.click(acceptBtn);

    await waitFor(() => {
      expect(api.resolveDisambiguationItem).toHaveBeenCalledWith("proj-1", "di-1", {
        status: "accepted",
        resolved_by: "user",
      });
    });
  });

  it("calls resolveDisambiguationItem on reject", async () => {
    vi.mocked(api.resolveDisambiguationItem).mockResolvedValue({ ...mockItems.items[0], status: "rejected" } as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("角色名")).toBeInTheDocument());

    const rejectBtn = screen.getByText("驳回");
    fireEvent.click(rejectBtn);

    await waitFor(() => {
      expect(api.resolveDisambiguationItem).toHaveBeenCalledWith("proj-1", "di-1", {
        status: "rejected",
        resolved_by: "user",
      });
    });
  });

  it("shows status badge for non-pending items", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("已采纳")).toBeInTheDocument();
    });
  });

  it("shows empty state when no items", async () => {
    vi.mocked(api.listDisambiguationItems).mockResolvedValue({ items: [], total: 0 });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("无待处理项")).toBeInTheDocument();
    });
  });

  it("includes ProjectNav", async () => {
    renderPage();
    await waitFor(() => {
      const links = screen.getAllByText("消歧队列");
      expect(links.length).toBeGreaterThanOrEqual(1);
    });
  });
});
