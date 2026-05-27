import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { DeconstructPage } from "./DeconstructPage";

const mockDeconstructStream = vi.fn();
const mockCreateProject = vi.fn();

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    deconstructStream: (...args: unknown[]) => mockDeconstructStream(...args),
    createProject: (...args: unknown[]) => mockCreateProject(...args),
  };
});

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe("DeconstructPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders idle state with input form", () => {
    render(<DeconstructPage />, { wrapper });
    expect(screen.getByText("参考书拆解")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("输入参考书的名称")).toBeInTheDocument();
    expect(screen.getByText("开始拆解分析")).toBeInTheDocument();
  });

  it("shows analyzing state after submitting", async () => {
    mockDeconstructStream.mockImplementation(async function* () {
      yield { status: "analyzing", message: "分析中..." };
      await new Promise((r) => setTimeout(r, 50));
    });

    render(<DeconstructPage />, { wrapper });

    const titleInput = screen.getByPlaceholderText("输入参考书的名称");
    fireEvent.change(titleInput, { target: { value: "测试书" } });

    const sampleInput = screen.getAllByPlaceholderText(/粘贴第/)[0];
    fireEvent.change(sampleInput, { target: { value: "这是一段测试样章" } });

    fireEvent.click(screen.getByText("开始拆解分析"));

    await waitFor(() => {
      expect(screen.getByText("正在分析参考书...")).toBeInTheDocument();
    });
  });

  it("shows preview with deconstruction tabs", async () => {
    mockDeconstructStream.mockImplementation(async function* () {
      yield { status: "analyzing", message: "分析中..." };
      yield {
        status: "done",
        deconstruction: {
          golden_chapters: ["第一章：主角登场，金手指觉醒"],
          hooks: ["悬念钩子：主角身世之谜"],
          character_patterns: ["废柴逆袭型主角"],
          world_patterns: ["修真等级制度"],
          pacing: ["快节奏开局"],
          transferable_patterns: ["金手指渐进升级", "门派竞争机制"],
          red_flags: ["不要复制具体角色名"],
        },
      };
    });

    render(<DeconstructPage />, { wrapper });

    fireEvent.change(screen.getByPlaceholderText("输入参考书的名称"), {
      target: { value: "测试书" },
    });
    fireEvent.change(screen.getAllByPlaceholderText(/粘贴第/)[0], {
      target: { value: "样章内容" },
    });

    const startBtns = screen.getAllByText("开始拆解分析");
    fireEvent.click(startBtns[startBtns.length - 1]);

    await waitFor(() => {
      expect(screen.getByText("《测试书》拆解结果")).toBeInTheDocument();
    });

    const tabs = screen.getAllByRole("tab");
    expect(tabs.length).toBeGreaterThan(0);
    expect(screen.getByText("金手指渐进升级")).toBeInTheDocument();
  });

  it("shows error state on failure", async () => {
    mockDeconstructStream.mockRejectedValue(new Error("Network error"));

    render(<DeconstructPage />, { wrapper });

    fireEvent.change(screen.getByPlaceholderText("输入参考书的名称"), {
      target: { value: "测试书" },
    });
    fireEvent.change(screen.getAllByPlaceholderText(/粘贴第/)[0], {
      target: { value: "样章" },
    });

    const startBtns = screen.getAllByText("开始拆解分析");
    fireEvent.click(startBtns[startBtns.length - 1]);

    await waitFor(() => {
      expect(screen.getByText("分析失败")).toBeInTheDocument();
    });
  });

  it("requires book title and sample before submit", () => {
    render(<DeconstructPage />, { wrapper });

    const startBtns = screen.getAllByText("开始拆解分析");
    fireEvent.click(startBtns[startBtns.length - 1]);

    // Should stay in idle, showing toast error (mocked)
    expect(screen.getByText("参考书拆解")).toBeInTheDocument();
  });
});
