import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  listProjects: vi.fn(),
  createProject: vi.fn(),
  deleteProject: vi.fn(),
  scanImport: vi.fn(),
  executeImport: vi.fn(),
}));

import * as api from "@/lib/api";
import { ProjectHub } from "./ProjectHub";

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ProjectHub />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const emptyList = { items: [], total: 0 };

describe("ProjectHub — import UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listProjects).mockResolvedValue(emptyList);
  });

  it("renders import button alongside create button", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("导入项目")).toBeInTheDocument();
    });
    expect(screen.getByText("新建项目")).toBeInTheDocument();
  });

  it("import dialog contains scan input and scan button", async () => {
    vi.mocked(api.listProjects).mockResolvedValue(emptyList);
    renderPage();
    await waitFor(() => screen.getByText("导入项目"));
    fireEvent.click(screen.getByText("导入项目"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/my-novel/)).toBeInTheDocument();
      expect(screen.getByText("扫描")).toBeInTheDocument();
    });
  });
});
