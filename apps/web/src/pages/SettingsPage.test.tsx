import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api", () => ({
  getLlmSettings: vi.fn(),
  updateLlmSettings: vi.fn(),
  testLlmConnection: vi.fn(),
}));

import * as api from "@/lib/api";
import { SettingsPage } from "./SettingsPage";

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const emptySettings = {
  id: "", user_id: "u1",
  api_key_masked: null, base_url: null, model: null,
  created_at: "", updated_at: "",
};

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton initially", () => {
    vi.mocked(api.getLlmSettings).mockReturnValue(new Promise(() => {}));
    renderPage();
    const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders form fields after loading", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue(emptySettings);
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText("API Key")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Base URL")).toBeInTheDocument();
    expect(screen.getByLabelText("Model")).toBeInTheDocument();
  });

  it("populates base_url and model from saved settings", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue({
      ...emptySettings, id: "s1",
      api_key_masked: "sk-...****...678",
      base_url: "https://api.openai.com/v1",
      model: "gpt-4o",
    });
    renderPage();

    await waitFor(() => {
      const baseUrlInput = screen.getByLabelText("Base URL") as HTMLInputElement;
      expect(baseUrlInput.value).toBe("https://api.openai.com/v1");
    });
    const modelInput = screen.getByLabelText("Model") as HTMLInputElement;
    expect(modelInput.value).toBe("gpt-4o");
  });

  it("has save and test buttons after loading", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue(emptySettings);
    renderPage();

    await waitFor(() => {
      const saveButtons = screen.getAllByText("保存设置");
      expect(saveButtons.length).toBeGreaterThan(0);
    });
    const testButtons = screen.getAllByText("测试连接");
    expect(testButtons.length).toBeGreaterThan(0);
  });

  it("calls updateLlmSettings on save", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue(emptySettings);
    vi.mocked(api.updateLlmSettings).mockResolvedValue({
      ...emptySettings, id: "s1",
      api_key_masked: "sk-...****...678",
      base_url: "https://api.openai.com/v1",
      model: "gpt-4o",
    });
    renderPage();

    await waitFor(() => screen.getByLabelText("API Key"));

    fireEvent.change(screen.getByLabelText("API Key"), { target: { value: "sk-test-key-123456" } });
    fireEvent.click(screen.getAllByText("保存设置")[0]);

    await waitFor(() => {
      expect(api.updateLlmSettings).toHaveBeenCalled();
      const call = vi.mocked(api.updateLlmSettings).mock.calls[0][0] as Record<string, string>;
      expect(call.api_key).toBe("sk-test-key-123456");
    });
  });

  it("shows test result on success", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue(emptySettings);
    vi.mocked(api.testLlmConnection).mockResolvedValue({
      success: true, message: "OK", elapsed_ms: 100,
    });
    renderPage();

    await waitFor(() => screen.getAllByText("测试连接").length > 0);
    fireEvent.click(screen.getAllByText("测试连接")[0]);

    await waitFor(() => {
      expect(screen.getByText("连接成功")).toBeInTheDocument();
    });
  });

  it("shows test result on failure", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue(emptySettings);
    vi.mocked(api.testLlmConnection).mockResolvedValue({
      success: false, message: "Invalid API key", elapsed_ms: 50,
    });
    renderPage();

    await waitFor(() => screen.getAllByText("测试连接").length > 0);
    fireEvent.click(screen.getAllByText("测试连接")[0]);

    await waitFor(() => {
      expect(screen.getByText("连接失败")).toBeInTheDocument();
      expect(screen.getByText("Invalid API key")).toBeInTheDocument();
    });
  });

  it("renders priority info", async () => {
    vi.mocked(api.getLlmSettings).mockResolvedValue(emptySettings);
    renderPage();

    await waitFor(() => {
      const titles = screen.getAllByText("优先级说明");
      expect(titles.length).toBeGreaterThan(0);
    });
    const userSettingTexts = screen.getAllByText(/用户设置/);
    expect(userSettingTexts.length).toBeGreaterThan(0);
  });
});
