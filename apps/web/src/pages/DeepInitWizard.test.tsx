import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, within, cleanup } from "@testing-library/react";
import { toast } from "sonner";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as api from "@/lib/api";
import { DeepInitWizard } from "./DeepInitWizard";

vi.mock("@/lib/api", () => ({
  createProject: vi.fn(),
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
      <MemoryRouter initialEntries={["/projects/new/wizard"]}>
        <Routes>
          <Route path="/projects/new/wizard" element={<DeepInitWizard />} />
          <Route path="/projects/:id/planning" element={<div data-testid="planning-page">规划中心</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

/** Get the most recently rendered wizard footer. */
function getFooter() {
  const footers = screen.getAllByTestId("wizard-footer");
  return footers[footers.length - 1];
}

/** Click the forward/submit button in the wizard footer. */
function clickNextBtn() {
  const footer = getFooter();
  const buttons = within(footer).getAllByRole("button");
  const nextBtn = buttons.find(b => b.textContent?.match(/下一步|创建项目/));
  if (!nextBtn) throw new Error("Could not find next/submit button");
  fireEvent.click(nextBtn);
}

const mockProject = {
  id: "proj-new",
  title: "测试书名",
  description: null,
  genre: "玄幻",
  status: "active",
  owner_id: "user-1",
  synopsis_json: null,
  root_dir: "/data/test-slug",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("DeepInitWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders the wizard with first step", () => {
    renderPage();
    expect(screen.getByText("新建项目向导")).toBeInTheDocument();
    expect(screen.getByLabelText(/题材/)).toBeInTheDocument();
    expect(screen.getByLabelText(/核心卖点/)).toBeInTheDocument();
    expect(getFooter()).toBeInTheDocument();
  });

  it("navigates through steps", async () => {
    renderPage();

    // Step 1: fill genre and hook
    fireEvent.change(screen.getByLabelText(/题材/), { target: { value: "玄幻" } });
    fireEvent.change(screen.getByLabelText(/核心卖点/), { target: { value: "重生修仙" } });
    clickNextBtn();

    // Step 2: protagonist
    await waitFor(() => {
      expect(screen.getByLabelText(/主角名/)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/主角名/), { target: { value: "叶凡" } });
    fireEvent.change(screen.getByLabelText(/主角特质/), { target: { value: "坚韧" } });
    clickNextBtn();

    // Step 3: world building
    await waitFor(() => {
      expect(screen.getByLabelText(/世界观描述/)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/世界观描述/), { target: { value: "修真世界" } });
    clickNextBtn();

    // Step 4: power system
    await waitFor(() => {
      expect(screen.getByLabelText(/力量体系描述/)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/力量体系描述/), { target: { value: "练气筑基" } });
    clickNextBtn();

    // Step 5: extras (title, golden finger, targets)
    await waitFor(() => {
      expect(screen.getByLabelText(/书名/)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/书名/), { target: { value: "测试书名" } });
    clickNextBtn();

    // Step 6: review — button now reads "创建项目"
    await waitFor(() => {
      expect(within(getFooter()).getAllByText("创建项目").length).toBeGreaterThan(0);
    });
    expect(screen.getByText(/玄幻/)).toBeInTheDocument();
  });

  it("shows gate check error when required fields missing", async () => {
    renderPage();
    // Navigate to last step without filling required fields
    for (let i = 0; i < 5; i++) {
      clickNextBtn();
    }
    await waitFor(() => {
      expect(within(getFooter()).getAllByText("创建项目").length).toBeGreaterThan(0);
    });
    clickNextBtn();

    // Should show error about missing fields
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
  });

  it("submits full premise and navigates to planning on success", async () => {
    const { createProject } = await import("@/lib/api");
    vi.mocked(createProject).mockResolvedValue(mockProject);

    renderPage();

    // Fill all required steps
    fireEvent.change(screen.getByLabelText(/题材/), { target: { value: "玄幻" } });
    fireEvent.change(screen.getByLabelText(/核心卖点/), { target: { value: "重生" } });
    clickNextBtn();

    await waitFor(() => { expect(screen.getByLabelText(/主角名/)).toBeInTheDocument(); });
    fireEvent.change(screen.getByLabelText(/主角名/), { target: { value: "叶凡" } });
    clickNextBtn();

    await waitFor(() => { expect(screen.getByLabelText(/世界观描述/)).toBeInTheDocument(); });
    fireEvent.change(screen.getByLabelText(/世界观描述/), { target: { value: "修真" } });
    clickNextBtn();

    await waitFor(() => { expect(screen.getByLabelText(/力量体系描述/)).toBeInTheDocument(); });
    fireEvent.change(screen.getByLabelText(/力量体系描述/), { target: { value: "练气" } });
    clickNextBtn();

    await waitFor(() => { expect(screen.getByLabelText(/书名/)).toBeInTheDocument(); });
    fireEvent.change(screen.getByLabelText(/书名/), { target: { value: "星辰变" } });
    clickNextBtn();

    await waitFor(() => { expect(within(getFooter()).getAllByText("创建项目").length).toBeGreaterThan(0); });
    clickNextBtn();

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "星辰变",
          genre: "玄幻",
          hook: "重生",
          protagonist: { name: "叶凡", traits: "" },
          world_building: { description: "修真", key_locations: "" },
          power_system: "练气",
        })
      );
    });
  });
});
