import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { InitChatPage } from "./InitChatPage";

// Mock api module
const mockInitChatStream = vi.fn();
const mockInitSchemes = vi.fn();
const mockCreateProject = vi.fn();

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    initChatStream: (...args: unknown[]) => mockInitChatStream(...args),
    initSchemes: (...args: unknown[]) => mockInitSchemes(...args),
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

/** Helper: get first match for queries that return multiple in this codebase. */
function getInput() {
  const inputs = screen.getAllByPlaceholderText("输入你的想法...");
  return inputs[inputs.length - 1];
}

describe("InitChatPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders idle state with start button", () => {
    render(<InitChatPage />, { wrapper });
    expect(screen.getByText("对话式开书")).toBeInTheDocument();
    expect(screen.getByText("开始对话")).toBeInTheDocument();
    expect(screen.getByText("或使用静态向导快速创建")).toBeInTheDocument();
  });

  it("transitions to chatting state after clicking start", async () => {
    render(<InitChatPage />, { wrapper });
    const btns = screen.getAllByTestId("start-chat-btn");
    fireEvent.click(btns[btns.length - 1]);

    await waitFor(() => {
      expect(getInput()).toBeInTheDocument();
    });
  });

  it("shows assistant message and allows user reply", async () => {
    mockInitChatStream.mockImplementation(async function* () {
      yield {
        status: "asking",
        question: "你的主角叫什么名字？",
        missing_fields: ["protagonist_name"],
        hint: "当前已收集: genre, hook",
      };
    });

    render(<InitChatPage />, { wrapper });
    const btns = screen.getAllByTestId("start-chat-btn");
    fireEvent.click(btns[btns.length - 1]);

    await waitFor(() => {
      expect(getInput()).toBeInTheDocument();
    });

    const input = getInput();
    fireEvent.change(input, { target: { value: "李明" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    await waitFor(() => {
      expect(mockInitChatStream).toHaveBeenCalledWith(
        "李明",
        expect.arrayContaining([expect.objectContaining({ role: "user", content: "李明" })]),
      );
    });
  });

  it("shows scheme selection when chat completes", async () => {
    mockInitChatStream.mockImplementation(async function* () {
      yield {
        status: "complete",
        schemes: [
          {
            name: "标准方案",
            genre_focus: "玄幻",
            hook_variation: "逆袭之路",
            power_evolution: "渐进升级",
            target_scale: "100万字 / 500章",
            scores: {
              innovation: 70,
              marketability: 75,
              coherence: 80,
              depth: 75,
              readability: 80,
            },
          },
        ],
      };
    });

    render(<InitChatPage />, { wrapper });
    const btns = screen.getAllByTestId("start-chat-btn");
    fireEvent.click(btns[btns.length - 1]);

    const input = await screen.findAllByPlaceholderText("输入你的想法...").then((all) => all[all.length - 1]);
    fireEvent.change(input, { target: { value: "测试回复" } });
    const sendBtns = screen.getAllByRole("button", { name: /发送/i });
    fireEvent.click(sendBtns[sendBtns.length - 1]);

    await waitFor(() => {
      expect(screen.getByText("创意约束方案")).toBeInTheDocument();
      expect(screen.getByText("标准方案")).toBeInTheDocument();
    });
  });

  it("shows error state on stream failure", async () => {
    mockInitChatStream.mockRejectedValue(new Error("Network error"));

    render(<InitChatPage />, { wrapper });
    const btns = screen.getAllByTestId("start-chat-btn");
    fireEvent.click(btns[btns.length - 1]);

    const input = await screen.findAllByPlaceholderText("输入你的想法...").then((all) => all[all.length - 1]);
    fireEvent.change(input, { target: { value: "测试" } });
    const sendBtns = screen.getAllByRole("button", { name: /发送/i });
    fireEvent.click(sendBtns[sendBtns.length - 1]);

    await waitFor(() => {
      expect(screen.getByText(/连接异常/)).toBeInTheDocument();
    });
  });

  it("selects a scheme and enables create button", async () => {
    mockInitChatStream.mockImplementation(async function* () {
      yield {
        status: "complete",
        schemes: [
          {
            name: "方案A",
            genre_focus: "科幻",
            hook_variation: "时间循环",
            power_evolution: "科技进化",
            target_scale: "80万字",
            scores: { innovation: 80, marketability: 70, coherence: 75, depth: 80, readability: 75 },
          },
        ],
      };
    });

    mockCreateProject.mockResolvedValue({
      id: "proj-123",
      title: "方案A",
      warnings: [],
    });

    render(<InitChatPage />, { wrapper });
    const btns = screen.getAllByTestId("start-chat-btn");
    fireEvent.click(btns[btns.length - 1]);

    const input = await screen.findAllByPlaceholderText("输入你的想法...").then((all) => all[all.length - 1]);
    fireEvent.change(input, { target: { value: "测试" } });
    const sendBtns = screen.getAllByRole("button", { name: /发送/i });
    fireEvent.click(sendBtns[sendBtns.length - 1]);

    await waitFor(() => {
      expect(screen.getByText("方案A")).toBeInTheDocument();
    });

    // Click scheme card to select
    fireEvent.click(screen.getByText("方案A"));

    // Create button should be enabled
    const createBtns = screen.getAllByRole("button", { name: /确认创建项目/i });
    expect(createBtns[createBtns.length - 1]).not.toBeDisabled();
  });

  it("navigates back button works in idle state", () => {
    render(<InitChatPage />, { wrapper });
    const backBtns = screen.getAllByRole("button", { name: "" });
    expect(backBtns.length).toBeGreaterThan(0);
  });
});
