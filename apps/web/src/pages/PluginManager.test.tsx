import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  listPlugins: vi.fn(),
  togglePlugin: vi.fn(),
  loadPlugin: vi.fn(),
  reloadPlugins: vi.fn(),
}));

import * as api from "@/lib/api";
import { PluginManager } from "./PluginManager";

const mockPlugins = {
  plugins: [
    {
      name: "combat_checker",
      display_name: "战斗一致性检查",
      version: "1.0.0",
      author: "NovelCraft",
      description: "检查战斗描写一致性",
      enabled: true,
      loaded: false,
      triggers: ["onChapterAccepted"],
    },
  ],
  total: 1,
};

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PluginManager />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PluginManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listPlugins).mockResolvedValue(mockPlugins);
    vi.mocked(api.togglePlugin).mockResolvedValue({ name: "combat_checker", enabled: false });
    vi.mocked(api.loadPlugin).mockResolvedValue({ name: "combat_checker", loaded: true });
    vi.mocked(api.reloadPlugins).mockResolvedValue({ discovered: 1, plugins: mockPlugins.plugins });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders plugin list", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("战斗一致性检查")).toBeInTheDocument();
    });
    expect(screen.getByText("1 个插件")).toBeInTheDocument();
  });

  it("calls togglePlugin when disable is clicked", async () => {
    renderPage();
    await waitFor(() => screen.getByText("禁用"));
    fireEvent.click(screen.getByText("禁用"));

    await waitFor(() => {
      expect(api.togglePlugin).toHaveBeenCalledWith("combat_checker", false);
    });
  });

  it("calls reloadPlugins when rescan is clicked", async () => {
    renderPage();
    await waitFor(() => expect(screen.getAllByRole("button", { name: /重新扫描/ }).length).toBeGreaterThan(0));
    fireEvent.click(screen.getAllByRole("button", { name: /重新扫描/ })[0]);

    await waitFor(() => {
      expect(api.reloadPlugins).toHaveBeenCalled();
    });
  });
});
