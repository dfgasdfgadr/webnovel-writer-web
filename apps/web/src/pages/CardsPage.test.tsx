import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CardsPage } from "./CardsPage";

vi.mock("@/lib/api", () => ({
  listCards: vi.fn().mockResolvedValue([
    { id: "c1", card_type: "character", label: "主角", content: { text: "测试内容" }, created_at: "2024-01-01" },
  ]),
  getProject: vi.fn().mockResolvedValue({
    id: "p1", title: "测试项目", status: "active", created_at: "2024-01-01", updated_at: "2024-01-01",
  }),
  createCard: vi.fn(),
  deleteCard: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/proj-1/cards"]}>
        <Routes>
          <Route path="/projects/:projectId/cards" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("CardsPage", () => {
  it("renders the page header", async () => {
    render(<CardsPage />, { wrapper });
    expect(await screen.findByRole("heading", { name: "设定卡片" })).toBeDefined();
  });

  it("renders tab triggers for each card type", async () => {
    render(<CardsPage />, { wrapper });
    const roles = await screen.findAllByRole("tab", { name: /角色/ });
    expect(roles.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("tab", { name: /势力/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("tab", { name: /规则/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("tab", { name: /道具/ }).length).toBeGreaterThanOrEqual(1);
  });

  it("shows create card button", async () => {
    render(<CardsPage />, { wrapper });
    const btns = await screen.findAllByText("新建卡片");
    expect(btns.length).toBeGreaterThanOrEqual(1);
  });

  it("renders loaded card label", async () => {
    render(<CardsPage />, { wrapper });
    const labels = await screen.findAllByText("主角");
    expect(labels.length).toBeGreaterThanOrEqual(1);
  });
});
