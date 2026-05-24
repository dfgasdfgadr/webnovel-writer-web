import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ projectId: "p1", chapterId: "c1" }),
  };
});

vi.mock("@/lib/api", () => ({
  getProject: vi.fn(),
  getChapter: vi.fn(),
  getReviews: vi.fn(),
}));

import * as api from "@/lib/api";
import { ReviewPage } from "./ReviewPage";

const mockProject = {
  id: "p1", title: "测试项目", description: null, genre: null,
  status: "writing", owner_id: "u1", created_at: "", updated_at: "",
};

const mockChapter = {
  id: "c1", project_id: "p1", title: "第一章", number: 1,
  content: "test", word_count: 100, status: "draft",
  created_at: "", updated_at: "",
};

const emptyReviews: api.ReviewIssue[] = [];
const mockReviews: api.ReviewIssue[] = [
  { id: "r1", severity: "blocking", category: "consistency", title: "角色性格矛盾", description: "主角在前半段冷酷无情，后半段突然热情。", evidence: "原文引用...", suggestion: "统一角色性格", is_fixed: false, created_at: "" },
  { id: "r2", severity: "major", category: "ooc", title: "配角行为不符", description: "配角行为与设定不符。", evidence: null, suggestion: "修改配角行为", is_fixed: false, created_at: "" },
  { id: "r3", severity: "minor", category: "style", title: "用词重复", description: "多次使用同一形容词。", evidence: null, suggestion: null, is_fixed: true, created_at: "" },
];

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ReviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeletons", () => {
    vi.mocked(api.getProject).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getChapter).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getReviews).mockReturnValue(new Promise(() => {}));
    renderPage();
    const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders empty state when no reviews", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue(emptyReviews);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("暂无审查问题")).toBeInTheDocument();
    });
  });

  it("renders review issues with severity", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue(mockReviews);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("角色性格矛盾")).toBeInTheDocument();
    });
    expect(screen.getByText("配角行为不符")).toBeInTheDocument();
    expect(screen.getByText("用词重复")).toBeInTheDocument();
  });

  it("shows summary count badges", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue(mockReviews);
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("审查中心").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("共 3 项")).toBeInTheDocument();
  });

  it("shows evidence blockquote when present", async () => {
    vi.mocked(api.getProject).mockResolvedValue(mockProject);
    vi.mocked(api.getChapter).mockResolvedValue(mockChapter);
    vi.mocked(api.getReviews).mockResolvedValue(mockReviews);
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText("原文引用...").length).toBeGreaterThan(0);
    });
  });
});
