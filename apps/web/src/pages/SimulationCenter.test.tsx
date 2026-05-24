import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

const mockProject = {
  id: "p1",
  title: "测试项目",
  volume_label: "第一卷",
  status: "writing",
  root_dir: "/tmp/p1",
  created_at: "2026-01-01T00:00:00",
  updated_at: "2026-01-01T00:00:00",
};

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ projectId: "p1" }),
  };
});

vi.mock("@/lib/api", () => ({
  getProject: vi.fn(),
}));

import * as api from "@/lib/api";
import { SimulationCenter } from "./SimulationCenter";

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SimulationCenter />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockFetch = vi.fn();

describe("SimulationCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    globalThis.fetch = mockFetch;
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });
  });

  it("renders page title and back link", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("测试项目")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "推演中心" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "项目列表" })).toBeInTheDocument();
  });

  it("renders mode selection cards", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("写前推演").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("分支探索").length).toBeGreaterThan(0);
  });

  it("shows empty state in report panel when no simulation", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("尚未创建推演").length).toBeGreaterThan(0);
    });
  });

  it("shows history tab", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("推演历史").length).toBeGreaterThan(0);
    });
  });

  it("disables submit button when sim brief is empty", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("写前推演").length).toBeGreaterThan(0);
    });
    const buttons = screen.getAllByText("开始推演");
    expect(buttons.length).toBeGreaterThan(0);
    const submitBtn = buttons[0].closest("button");
    expect(submitBtn).toBeTruthy();
    expect((submitBtn as HTMLButtonElement).disabled).toBe(true);
  });
});
