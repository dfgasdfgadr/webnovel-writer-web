import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "./LoginPage";

const mockLogin = vi.fn();
const mockRegister = vi.fn();

vi.mock("@/stores/auth", () => ({
  useAuthStore: (selector: (s: unknown) => unknown) => {
    const store = { login: mockLogin, register: mockRegister };
    return selector(store);
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders login form by default", () => {
    renderLoginPage();
    expect(screen.getByText("NovelCraft")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /登录/ })).toBeInTheDocument();
    expect(screen.getByLabelText("用户名")).toBeInTheDocument();
    expect(screen.getByLabelText("密码")).toBeInTheDocument();
  });

  it("renders register toggle link", () => {
    renderLoginPage();
    expect(screen.getByText(/还没有账号/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "注册" })).toBeInTheDocument();
  });

  it("switches to register mode on toggle click", () => {
    renderLoginPage();
    fireEvent.click(screen.getByRole("button", { name: "注册" }));
    expect(screen.getByText("创建你的创作账号")).toBeInTheDocument();
    expect(screen.getByLabelText("显示名称（选填）")).toBeInTheDocument();
    expect(screen.getByText(/已有账号/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "登录" })).toBeInTheDocument();
  });

  it("switches back to login mode on toggle click from register", () => {
    renderLoginPage();
    fireEvent.click(screen.getByRole("button", { name: "注册" }));
    fireEvent.click(screen.getByRole("button", { name: "登录" }));
    expect(screen.getByText("登录你的写作工作台")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /登录/ })).toBeInTheDocument();
  });

  it("displays dev credentials hint in login mode", () => {
    renderLoginPage();
    const spans = screen.getAllByText(/admin/i);
    expect(spans.length).toBeGreaterThanOrEqual(2); // admin + admin123456
  });

  it("hides dev credentials hint in register mode", () => {
    renderLoginPage();
    fireEvent.click(screen.getByRole("button", { name: "注册" }));
    expect(screen.queryByText(/pnpm seed/)).not.toBeInTheDocument();
  });

  it("calls login on form submit", async () => {
    mockLogin.mockResolvedValue(undefined);
    renderLoginPage();

    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "password" } });
    fireEvent.click(screen.getByRole("button", { name: /登录/ }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("admin", "password");
    });
  });

  it("calls register on form submit in register mode", async () => {
    mockRegister.mockResolvedValue(undefined);
    renderLoginPage();
    fireEvent.click(screen.getByRole("button", { name: "注册" }));

    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "newuser" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "secret123" } });
    fireEvent.change(screen.getByLabelText("显示名称（选填）"), { target: { value: "笔名" } });
    fireEvent.click(screen.getByRole("button", { name: "注册" }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith("newuser", "secret123", "笔名");
    });
  });

  it("navigates to / on successful login", async () => {
    mockLogin.mockResolvedValue(undefined);
    renderLoginPage();

    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "password" } });
    fireEvent.click(screen.getByRole("button", { name: /登录/ }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });
});
