import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  listWorkflows: vi.fn(),
  listProjects: vi.fn(),
  getBackupStatus: vi.fn(),
  getWorkflowHistory: vi.fn(),
  toggleWorkflowRule: vi.fn(),
}));

import * as api from "@/lib/api";
import { WorkflowView } from "./WorkflowView";

const mockRules = {
  rules: [
    {
      name: "章节通过后剧情推演",
      trigger: "onChapterAccepted",
      enabled: true,
      actions: [{ name: "pre_chapter_sim", type: "sim", config: {} }],
      condition: {},
    },
    {
      name: "章节通过后自动备份",
      trigger: "onChapterAccepted",
      enabled: true,
      actions: [{ name: "git_auto_backup", type: "git_backup", config: { auto_init: true } }],
      condition: {},
    },
  ],
  total: 2,
  builtin_count: 2,
};

const mockProjects = {
  items: [{ id: "p1", title: "测试项目", status: "writing" }],
  total: 1,
};

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <WorkflowView />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkflowView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listWorkflows).mockResolvedValue(mockRules);
    vi.mocked(api.listProjects).mockResolvedValue(mockProjects);
    vi.mocked(api.getBackupStatus).mockResolvedValue({
      enabled: true,
      status: "completed",
      last_run: "2026-05-27T10:00:00Z",
      chapter_num: "1",
      total_runs: 1,
    });
    vi.mocked(api.getWorkflowHistory).mockResolvedValue({
      runs: [
        {
          timestamp: "2026-05-27T10:00:00Z",
          trigger: "onChapterAccepted",
          action: "git_backup",
          status: "completed",
          chapter_num: "1",
        },
      ],
      total: 1,
    });
    vi.mocked(api.toggleWorkflowRule).mockResolvedValue({ name: "章节通过后剧情推演", enabled: false });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders workflow rules with trigger labels", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("章节通过后剧情推演")).toBeInTheDocument();
    });
    expect(screen.getByText("章节通过后自动备份")).toBeInTheDocument();
    expect(screen.getAllByText("章节通过后").length).toBeGreaterThan(0);
  });

  it("shows backup status after selecting a project", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "测试项目" })).toBeInTheDocument();
    });

    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "p1" } });

    await waitFor(() => {
      expect(api.getBackupStatus).toHaveBeenCalledWith("p1");
      expect(screen.getByText("备份成功")).toBeInTheDocument();
    });
  });

  it("shows execution history after selecting a project", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "测试项目" })).toBeInTheDocument();
    });

    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "p1" } });

    await waitFor(() => {
      expect(api.getWorkflowHistory).toHaveBeenCalledWith("p1", 10);
      expect(screen.getByText("git_backup")).toBeInTheDocument();
    });
  });

  it("renders rule toggle switches", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText("禁用 章节通过后剧情推演")).toBeInTheDocument();
      expect(screen.getByLabelText("禁用 章节通过后自动备份")).toBeInTheDocument();
    });
  });
});
