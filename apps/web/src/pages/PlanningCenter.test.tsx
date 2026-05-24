import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
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

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/proj-1/planning"]}>
        <Routes>
          <Route path="/projects/:projectId/planning" element={<PlanningCenter />} />
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
  synopsis_json: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockSynopsis = {
  title: "星辰变",
  genre: "玄幻",
  hook: "一个不能修炼的少年，意外获得星辰之力",
  synopsis: "少年林凡在家族被灭后，意外觉醒星辰血脉，踏上复仇之路。",
  volumes: [
    { num: 1, title: "觉醒篇", summary: "林凡觉醒星辰血脉，踏入修炼之路", target_chapters: 50 },
  ],
};

const mockProjectWithSynopsis = {
  ...mockProject,
  synopsis_json: JSON.stringify(mockSynopsis),
};

const mockOutline = {
  chapter_num: 1,
  title: "星辰觉醒",
  outline: "林凡在家族矿场劳作时，意外发现一块星辰碎片，触碰后体内血脉被激活。",
  must_cover_nodes: ["发现星辰碎片", "血脉激活的异象"],
  forbidden_zones: ["不要过早暴露真实身份"],
  key_characters: [{ name: "林凡", role_in_chapter: "主角觉醒" }],
  target_words: 3000,
};

const mockBatchResult = {
  total: 3,
  completed: 3,
  failed: 0,
  results: [
    { chapter_num: 1, success: true, data: { ...mockOutline, chapter_num: 1 } },
    { chapter_num: 2, success: true, data: { ...mockOutline, chapter_num: 2, title: "修炼初成" } },
    { chapter_num: 3, success: true, data: { ...mockOutline, chapter_num: 3, title: "离开矿场" } },
  ],
};

const mockVolumePlan = {
  total_volumes: 2,
  volumes: [
    {
      num: 1, title: "觉醒篇", summary: "林凡觉醒星辰血脉", target_chapters: 50,
      chapters: [mockOutline],
    },
    {
      num: 2, title: "崛起篇", summary: "林凡进入宗门修炼", target_chapters: 50,
    },
  ],
};

describe("PlanningCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
  });

  afterEach(() => {
    cleanup();
  });

  it("renders page header and loading state", async () => {
    vi.mocked(api.getProject).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByRole("heading", { name: "规划中心" })).toBeInTheDocument();
  });

  it("renders project title after load", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("测试项目")).toBeInTheDocument();
    });
  });

  it("shows ProjectNav with planning tab active", async () => {
    renderPage();
    await waitFor(() => {
      const links = screen.getAllByText("规划中心");
      expect(links.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("has all 4 tab triggers", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());
    expect(screen.getByText("总纲")).toBeInTheDocument();
    expect(screen.getByText("章纲")).toBeInTheDocument();
    expect(screen.getByText("批量章纲")).toBeInTheDocument();
    expect(screen.getByText("卷纲规划")).toBeInTheDocument();
  });

  // ─── Synopsis Tab ───
  it("synopsis: shows form inputs", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    expect(screen.getByLabelText("题材")).toBeInTheDocument();
    expect(screen.getByLabelText("核心卖点")).toBeInTheDocument();
    expect(screen.getByLabelText("主角名")).toBeInTheDocument();
    expect(screen.getByLabelText("主角特质")).toBeInTheDocument();
    expect(screen.getByLabelText("世界观")).toBeInTheDocument();
    expect(screen.getByLabelText("力量体系")).toBeInTheDocument();
    expect(screen.getByText("生成总纲")).toBeInTheDocument();
  });

  it("synopsis: calls generateSynopsis on button click", async () => {
    vi.mocked(api.generateSynopsis).mockResolvedValue(mockSynopsis as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("题材"), { target: { value: "玄幻" } });
    fireEvent.click(screen.getByText("生成总纲"));

    await waitFor(() => {
      expect(api.generateSynopsis).toHaveBeenCalledWith("proj-1", expect.objectContaining({
        genre: "玄幻",
      }));
    });
  });

  it("synopsis: displays saved synopsis from project", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProjectWithSynopsis);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("星辰变")).toBeInTheDocument();
    });
    expect(screen.getByText("玄幻")).toBeInTheDocument();
    expect(screen.getByText("少年林凡在家族被灭后，意外觉醒星辰血脉，踏上复仇之路。")).toBeInTheDocument();
  });

  // ─── Outline Tab ───
  it("outline: shows form and generates", async () => {
    vi.mocked(api.generateOutline).mockResolvedValue(mockOutline as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("章纲"));

    await waitFor(() => {
      expect(screen.getByText("生成第1章章纲")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("生成第1章章纲"));

    await waitFor(() => {
      expect(api.generateOutline).toHaveBeenCalledWith("proj-1", expect.objectContaining({
        chapter_num: 1,
      }));
    });
  });

  it("outline: shows warning when no synopsis", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("章纲"));

    await waitFor(() => {
      expect(screen.getByText(/建议先生成总纲/)).toBeInTheDocument();
    });
  });

  // ─── Batch Tab ───
  it("batch: shows form inputs", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("批量章纲"));

    await waitFor(() => {
      expect(screen.getByLabelText("起始章节")).toBeInTheDocument();
      expect(screen.getByLabelText("结束章节")).toBeInTheDocument();
    });
  });

  it("batch: calls generateBatchOutlines", async () => {
    vi.mocked(api.generateBatchOutlines).mockResolvedValue(mockBatchResult as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("批量章纲"));

    await waitFor(() => {
      expect(screen.getByText(/生成第1–10章章纲/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/生成第1–10章章纲/));

    await waitFor(() => {
      expect(api.generateBatchOutlines).toHaveBeenCalledWith("proj-1", expect.objectContaining({
        start_chapter: 1,
        end_chapter: 10,
      }));
    });
  });

  it("batch: shows results after generation", async () => {
    vi.mocked(api.generateBatchOutlines).mockResolvedValue(mockBatchResult as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("批量章纲"));
    await waitFor(() => screen.getByText(/生成第1–10章章纲/));
    fireEvent.click(screen.getByText(/生成第1–10章章纲/));

    await waitFor(() => {
      expect(screen.getByText("星辰觉醒")).toBeInTheDocument();
    });
  });

  // ─── Volume Plan Tab ───
  it("volume-plan: shows form inputs", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProjectWithSynopsis);
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("卷纲规划"));

    await waitFor(() => {
      expect(screen.getByLabelText("总章节数")).toBeInTheDocument();
      expect(screen.getByLabelText("每卷章节数")).toBeInTheDocument();
    });
  });

  it("volume-plan: requires synopsis before generating", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("卷纲规划"));

    await waitFor(() => {
      expect(screen.getByText(/请先生成总纲/)).toBeInTheDocument();
    });
  });

  it("volume-plan: calls generateVolumePlan", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProjectWithSynopsis);
    vi.mocked(api.generateVolumePlan).mockResolvedValue(mockVolumePlan as any);
    renderPage();
    await waitFor(() => expect(screen.getByText("测试项目")).toBeInTheDocument());

    fireEvent.click(screen.getByText("卷纲规划"));

    await waitFor(() => screen.getByText("生成卷纲规划"));
    fireEvent.click(screen.getByText("生成卷纲规划"));

    await waitFor(() => {
      expect(api.generateVolumePlan).toHaveBeenCalledWith("proj-1", expect.objectContaining({
        total_chapters: 100,
        chapters_per_volume: 50,
      }));
    });
  });
});
