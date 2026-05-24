import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the api module before importing the store
vi.mock("@/lib/api", () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
}));

import { useAuthStore } from "./auth";
import * as api from "@/lib/api";

function resetStore() {
  useAuthStore.setState({
    user: null,
    token: localStorage.getItem("token"),
    isLoading: true,
    isAuthenticated: false,
  });
}

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    resetStore();
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("has null user by default", () => {
      const { user } = useAuthStore.getState();
      expect(user).toBeNull();
    });

    it("reads token from localStorage", () => {
      localStorage.setItem("token", "stored-token");
      resetStore();
      const { token } = useAuthStore.getState();
      expect(token).toBe("stored-token");
    });

    it("isAuthenticated is false by default", () => {
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe("login", () => {
    it("sets token, user, and isAuthenticated on success", async () => {
      vi.mocked(api.login).mockResolvedValue({ access_token: "jwt", token_type: "bearer" });
      vi.mocked(api.getMe).mockResolvedValue({
        id: "u1",
        username: "admin",
        display_name: null,
        created_at: "2024-01-01T00:00:00",
      });

      await useAuthStore.getState().login("admin", "password");

      const state = useAuthStore.getState();
      expect(state.token).toBe("jwt");
      expect(state.isAuthenticated).toBe(true);
      expect(state.user?.username).toBe("admin");
      expect(localStorage.getItem("token")).toBe("jwt");
    });

    it("login throws on failure", async () => {
      vi.mocked(api.login).mockRejectedValue(new Error("Invalid credentials"));

      await expect(
        useAuthStore.getState().login("admin", "wrong")
      ).rejects.toThrow("Invalid credentials");
    });
  });

  describe("register", () => {
    it("calls api.register then api.login", async () => {
      vi.mocked(api.register).mockResolvedValue({
        id: "u2",
        username: "newuser",
        display_name: null,
        created_at: "2024-01-01T00:00:00",
      });
      vi.mocked(api.login).mockResolvedValue({ access_token: "jwt2", token_type: "bearer" });
      vi.mocked(api.getMe).mockResolvedValue({
        id: "u2",
        username: "newuser",
        display_name: null,
        created_at: "2024-01-01T00:00:00",
      });

      await useAuthStore.getState().register("newuser", "password");

      expect(api.register).toHaveBeenCalledWith("newuser", "password", undefined);
      expect(api.login).toHaveBeenCalledWith("newuser", "password");
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });
  });

  describe("logout", () => {
    it("clears token, user, and isAuthenticated", () => {
      useAuthStore.setState({
        user: { id: "u1", username: "admin", display_name: null, created_at: "..." },
        token: "jwt",
        isAuthenticated: true,
      });

      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(localStorage.getItem("token")).toBeNull();
    });
  });

  describe("checkAuth", () => {
    it("sets isLoading false immediately when no token", async () => {
      useAuthStore.setState({ token: null });

      await useAuthStore.getState().checkAuth();

      expect(useAuthStore.getState().isLoading).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });

    it("fetches user when token exists", async () => {
      useAuthStore.setState({ token: "valid" });
      vi.mocked(api.getMe).mockResolvedValue({
        id: "u1",
        username: "admin",
        display_name: null,
        created_at: "2024-01-01T00:00:00",
      });

      await useAuthStore.getState().checkAuth();

      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it("clears token on fetch failure", async () => {
      useAuthStore.setState({ token: "expired" });
      vi.mocked(api.getMe).mockRejectedValue(new Error("401"));

      await useAuthStore.getState().checkAuth();

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
      expect(localStorage.getItem("token")).toBeNull();
    });
  });
});
