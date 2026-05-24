import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as api from "@/lib/api";
import { ChapterEditor } from "./ChapterEditor";

vi.mock("@/lib/api", () => ({
  getProject: vi.fn(),
  listChapters: vi.fn(),
  getChapter: vi.fn(),
  getReviews: vi.fn(),
  getLlmSettings: vi.fn(),
  updateChapter: vi.fn(),
  runPipeline: vi.fn(),
  createChapter: vi.fn(),
  deleteChapter: vi.fn(),
  streamDraftUrl: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const mockChapter = {
  id: "ch-1",
  project_id: "proj-1",
  title: "第一章 测试",
  number: 1,
  content: "这是测试内容。",
  outline: "",
  word_count: 7,
  status: "draft",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

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

const mockChaptersList = {
  items: [mockChapter],
  total: 1,
};

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function renderChapterEditor(route = "/projects/proj-1/chapters/ch-1") {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/projects/:projectId/chapters/:chapterId" element={<ChapterEditor />} />
          <Route path="/projects/:projectId" element={<ChapterEditor />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ChapterEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getLlmSettings).mockResolvedValue({
      user_id: "user-1",
      api_key_masked: null,
      base_url: null,
      model: null,
      updated_at: null,
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("mounts without throwing", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "第一章 测试" })).toBeInTheDocument();
    });
  });

  it("loads and displays chapter content in textarea", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    await waitFor(() => {
      const textarea = screen.getByPlaceholderText(/开始写作/);
      expect(textarea).toHaveValue("这是测试内容。");
    });
  });

  it("shows word count badge", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByText("7 字")).toBeInTheDocument();
    });
  });

  it("shows empty state when no chapterId", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);

    renderChapterEditor("/projects/proj-1");

    await waitFor(() => {
      expect(screen.getByText("选择一个章节")).toBeInTheDocument();
    });
  });

  it("syncs content to textarea when chapter loads", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue({
      ...mockChapter,
      title: "特殊章节",
      content: "这是异步加载的内容。",
      word_count: 10,
    });
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "特殊章节" })).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/开始写作/);
    expect(textarea).toHaveValue("这是异步加载的内容。");
  });

  it("handles chapter with empty content", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue({
      ...mockChapter,
      content: "",
      word_count: 0,
    });
    vi.mocked(api.getReviews).mockResolvedValue([]);

    // Should not throw "Too many re-renders"
    expect(() => renderChapterEditor()).not.toThrow();
  });

  it("shows skeleton loading state", () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockReturnValue(new Promise(() => {})); // never resolves
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    // Skeletons should be present while chapter is loading
    const skeletons = document.querySelectorAll("[data-slot=skeleton]");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows save button", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByText("保存")).toBeInTheDocument();
    });
  });

  it("shows AI generate and pipeline buttons", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue([]);

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByText("AI 生成")).toBeInTheDocument();
      expect(screen.getByText("流水线")).toBeInTheDocument();
    });
  });

  it("blocks AI generate when outline is empty", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue({ ...mockChapter, outline: "" });
    vi.mocked(api.getReviews).mockResolvedValue([]);
    vi.mocked(api.getLlmSettings).mockResolvedValue({
      user_id: "user-1",
      api_key_masked: "sk-****1234",
      base_url: "https://api.example.com/v1",
      model: "gpt-4o",
      updated_at: null,
    });
    vi.mocked(api.streamDraftUrl).mockReturnValue("/api/v1/agents/pipeline/ch-1/stream");

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByText("AI 生成")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("AI 生成"));
    expect(api.streamDraftUrl).not.toHaveBeenCalled();
  });

  it("loads saved outline and saves outline on button click", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.listChapters).mockResolvedValue(mockChaptersList);
    vi.mocked(api.getChapter).mockResolvedValue({
      ...mockChapter,
      outline: "已有章纲",
    });
    vi.mocked(api.getReviews).mockResolvedValue([]);
    vi.mocked(api.updateChapter).mockResolvedValue({
      ...mockChapter,
      outline: "更新后的章纲",
    });

    renderChapterEditor();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "第一章 测试" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("章纲"));

    const outlineInput = await screen.findByPlaceholderText(/输入章纲/);
    expect(outlineInput).toHaveValue("已有章纲");

    fireEvent.change(outlineInput, { target: { value: "更新后的章纲" } });
    fireEvent.click(screen.getByText("保存"));

    await waitFor(() => {
      expect(api.updateChapter).toHaveBeenCalledWith("proj-1", "ch-1", {
        outline: "更新后的章纲",
      });
    });
  });
});
