import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { StoryFoundryPage } from "./StoryFoundryPage";

const mockFoundryDeconstruct = vi.fn();
const mockFoundryQuestions = vi.fn();
const mockFoundryCompose = vi.fn();
const mockCreateProject = vi.fn();

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    foundryDeconstruct: (...args: unknown[]) => mockFoundryDeconstruct(...args),
    foundryQuestions: (...args: unknown[]) => mockFoundryQuestions(...args),
    foundryCompose: (...args: unknown[]) => mockFoundryCompose(...args),
    createProject: (...args: unknown[]) => mockCreateProject(...args),
  };
});

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <StoryFoundryPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockDeconstruction = {
  golden_chapters: ["黄金三章分析"],
  hooks: ["悬念钩子"],
  character_patterns: ["成长型主角"],
  world_patterns: ["逐步揭秘"],
  pacing: ["快节奏"],
  transferable_patterns: ["模式1", "模式2"],
  red_flags: ["避免抄袭"],
};

const mockQuestionSets = [
  {
    id: "protagonist_core",
    title: "主角核心驱动力",
    description: "主角最核心的动机",
    options: [
      { id: "revenge", label: "复仇型", description: "复仇", effects: {} },
      { id: "ambition", label: "野心型", description: "野心", effects: {} },
    ],
  },
];

const mockComposeResult = {
  premise: { title: "测试书", genre: "玄幻", hook: "测试", target_words: 1000000, target_chapters: 300 },
  master_setting: { title: "测试书", world_overview: "世界观" },
  synopsis: { title: "测试书", synopsis: "概述", volumes: [{ num: 1, title: "第一卷", summary: "测试", target_chapters: 30 }] },
  first_volume_chapters: [
    { chapter_num: 1, title: "第一章", outline: "开篇", must_cover_nodes: ["出场"], forbidden_zones: [], key_characters: [], target_words: 3000 },
  ],
  fallback: false,
};

describe("StoryFoundryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders input step with title and sample inputs", () => {
    renderPage();
    expect(screen.getAllByRole("heading", { name: /AI 智能造书/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByPlaceholderText("输入参考书的名称").length).toBeGreaterThanOrEqual(1);
  });

  it("can add a sample chapter", () => {
    renderPage();
    expect(screen.getAllByText(/样章 1/).length).toBeGreaterThanOrEqual(1);
    const addButtons = screen.getAllByText("+ 添加样章");
    fireEvent.click(addButtons[0]);
    expect(screen.getAllByText(/样章 2/).length).toBeGreaterThanOrEqual(1);
  });

  it("transitions through deconstruct to preview flow", async () => {
    mockFoundryDeconstruct.mockResolvedValue({
      status: "done",
      deconstruction: mockDeconstruction,
      fallback: false,
    });
    mockFoundryQuestions.mockResolvedValue({
      question_sets: mockQuestionSets,
      fallback: false,
    });
    mockFoundryCompose.mockResolvedValue(mockComposeResult);
    mockCreateProject.mockResolvedValue({ id: "test-id", title: "测试书" });

    renderPage();

    // Input step - fill and submit
    fireEvent.change(screen.getAllByPlaceholderText("输入参考书的名称")[0], {
      target: { value: "测试书" },
    });
    fireEvent.change(screen.getAllByPlaceholderText("粘贴第 1 段样章文本...")[0], {
      target: { value: "样章内容..." },
    });
    const analyzeButtons = screen.getAllByRole("button", { name: /开始分析并生成选择题/ });
    fireEvent.click(analyzeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/拆解结果/)).toBeInTheDocument();
    });

    // Deconstruction step - click next
    const nextButtons = screen.getAllByRole("button", { name: /下一步：策略选择/ });
    fireEvent.click(nextButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("创作策略选择")).toBeInTheDocument();
    });

    // Questions step - select option
    const option = screen.getByText("复仇型");
    fireEvent.click(option);

    const composeButtons = screen.getAllByRole("button", { name: /生成完整设定/ });
    fireEvent.click(composeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("设定预览")).toBeInTheDocument();
    });

    // Preview step - create project
    const createButtons = screen.getAllByRole("button", { name: /确认并创建项目/ });
    fireEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("项目创建成功！")).toBeInTheDocument();
    });
  });

  it("renders deconstruction tabs with transferable patterns", async () => {
    mockFoundryDeconstruct.mockResolvedValue({
      status: "done",
      deconstruction: mockDeconstruction,
      fallback: false,
    });
    mockFoundryQuestions.mockResolvedValue({
      question_sets: [],
      fallback: false,
    });

    renderPage();

    fireEvent.change(screen.getAllByPlaceholderText("输入参考书的名称")[0], {
      target: { value: "测试书" },
    });
    fireEvent.change(screen.getAllByPlaceholderText("粘贴第 1 段样章文本...")[0], {
      target: { value: "内容" },
    });
    const analyzeButtons = screen.getAllByRole("button", { name: /开始分析并生成选择题/ });
    fireEvent.click(analyzeButtons[0]);

    await waitFor(() => {
      expect(screen.getAllByText("可迁移模式").length).toBeGreaterThanOrEqual(1);
    });
  });
});
