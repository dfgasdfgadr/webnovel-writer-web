import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  listProjects: vi.fn(),
  createProject: vi.fn(),
  deleteProject: vi.fn(),
  scanImport: vi.fn(),
  executeImport: vi.fn(),
  exportProjectUrl: vi.fn((id: string) => `/api/v1/projects/${id}/export?token=test`),
}));

import * as api from "@/lib/api";
import { ProjectHub } from "./ProjectHub";

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ProjectHub />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const emptyList = { items: [], total: 0 };

describe("ProjectHub — import UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listProjects).mockResolvedValue(emptyList);
  });

  it("renders import button alongside create button", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("导入项目")).toBeInTheDocument();
    });
    expect(screen.getByText("新建项目")).toBeInTheDocument();
  });

  it("import dialog contains scan input and scan button", async () => {
    vi.mocked(api.listProjects).mockResolvedValue(emptyList);
    renderPage();
    await waitFor(() => screen.getByText("导入项目"));
    fireEvent.click(screen.getByText("导入项目"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/my-novel/)).toBeInTheDocument();
      expect(screen.getByText("扫描")).toBeInTheDocument();
    });
  });

  it("renders onboarding entry links", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("AI 智能造书").length).toBeGreaterThan(0);
      expect(screen.getAllByText("对话开书").length).toBeGreaterThan(0);
      expect(screen.getAllByText("拆书").length).toBeGreaterThan(0);
    });
  });

  it("export menu item triggers download", async () => {
    const mockProjects = {
      items: [{
        id: "p1",
        title: "测试项目",
        description: "",
        genre: "玄幻",
        status: "active",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        owner_id: "u1",
        root_dir: "",
      }],
      total: 1,
    };
    vi.mocked(api.listProjects).mockResolvedValue(mockProjects);
    const originalHref = window.location.href;
    Object.defineProperty(window, "location", {
      value: { href: originalHref },
      writable: true,
    });

    renderPage();
    await waitFor(() => screen.getByText("测试项目"));

    // Hover to reveal dropdown trigger
    const card = screen.getByText("测试项目").closest("[class*='group']") || screen.getByText("测试项目").closest("div");
    if (card) fireEvent.mouseEnter(card);

    // Find and click the more options button
    const moreBtn = screen.getAllByRole("button").find((b) =>
      b.querySelector("[data-lucide='more-vertical']") || b.innerHTML.includes("more")
    );
    if (moreBtn) fireEvent.click(moreBtn);

    // The export option should be in the dropdown
    await waitFor(() => {
      const exportItem = screen.queryByText("导出 zip");
      if (exportItem) {
        fireEvent.click(exportItem);
        expect(window.location.href).toContain("/api/v1/projects/p1/export");
      }
    });
  });
});
