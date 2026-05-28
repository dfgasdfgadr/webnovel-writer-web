import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  getProjectPrompts: vi.fn(),
  updateProjectPrompt: vi.fn(),
  resetProjectPrompt: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useParams: () => ({ projectId: "p1" }) };
});

import * as api from "@/lib/api";
import { PromptWorkshop } from "./PromptWorkshop";

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PromptWorkshop />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockPrompts = {
  prompts: [
    { scope: "reader_pulse", key: "system_prompt", content: "test prompt", is_default: true },
    { scope: "review", key: "system_prompt", content: "review prompt", is_default: false },
    { scope: "polish", key: "system_prompt", content: "polish prompt", is_default: true },
  ],
};

describe("PromptWorkshop", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getProjectPrompts).mockResolvedValue(mockPrompts);
  });

  it("renders scope tabs", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("读者模拟")).toBeInTheDocument();
      expect(screen.getByText("审查")).toBeInTheDocument();
      expect(screen.getByText("润色")).toBeInTheDocument();
    });
  });

  it("shows default badge for default prompts", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("默认")).toBeInTheDocument();
    });
  });

  it("renders save and reset buttons", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("保存")).toBeInTheDocument();
      expect(screen.getByText("恢复默认")).toBeInTheDocument();
    });
  });
});
