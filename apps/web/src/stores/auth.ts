import { create } from "zustand";
import type { UserPublic } from "@/lib/api";
import { getMe, login as apiLogin, register as apiRegister, type TokenResponse } from "@/lib/api";

interface AuthState {
  user: UserPublic | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, displayName?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem("token"),
  isLoading: true,
  isAuthenticated: false,

  login: async (username, password) => {
    const data: TokenResponse = await apiLogin(username, password);
    localStorage.setItem("token", data.access_token);
    set({ token: data.access_token });
    const user = await getMe();
    set({ user, isAuthenticated: true });
  },

  register: async (username, password, displayName) => {
    await apiRegister(username, password, displayName);
    await get().login(username, password);
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null, token: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = get().token;
    if (!token) {
      set({ isLoading: false });
      return;
    }
    try {
      const user = await getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
