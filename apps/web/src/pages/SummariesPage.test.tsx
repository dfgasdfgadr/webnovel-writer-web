import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SummariesPage } from "./SummariesPage";

vi.mock("@/lib/api", () => ({
  listSummaries: vi.fn().mockResolvedValue([
    { id: "s1", project_id: "p1", level: "chapter", scope_label: "第1章", parent_id: null, title: "开场", content: "测试摘要", created_at: "2024-01-01", updated_at: "2024-01-01" },
  ]),
  getProject: vi.fn().mockResolvedValue({
    id: "p1", title: "测试项目", status: "active", created_at: "2024-01-01", updated_at: "2024-01-01",
  }),
  createSummary: vi.fn(),
  updateSummary: vi.fn(),
  deleteSummary: vi.fn(),
  generateSummary: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/proj-1/summaries"]}>
        <Routes>
          <Route path="/projects/:projectId/summaries" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("SummariesPage", () => {
  it("renders the page header", async () => {
    render(<SummariesPage />, { wrapper });
    expect(await screen.findByRole("heading", { name: "三级摘要" })).toBeDefined();
  });

  it("renders level tab triggers", async () => {
    render(<SummariesPage />, { wrapper });
    const chapterTabs = await screen.findAllByRole("tab", { name: /章/ });
    expect(chapterTabs.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("tab", { name: /故事弧/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("tab", { name: /卷/ }).length).toBeGreaterThanOrEqual(1);
  });

  it("shows new summary button", async () => {
    render(<SummariesPage />, { wrapper });
    const btns = await screen.findAllByText("新建摘要");
    expect(btns.length).toBeGreaterThanOrEqual(1);
  });
});
