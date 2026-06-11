/**
 * Auth Zustand store.
 * Persists JWT token and user info to localStorage.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserResponse } from "@/types/api";

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (token: string, user: UserResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: (token, user) => {
        // Store in localStorage for axios interceptor
        localStorage.setItem("ai_librarian_token", token);
        localStorage.setItem("ai_librarian_user", JSON.stringify(user));
        // Also set a cookie so Next.js middleware can read it server-side
        document.cookie = `ai_librarian_token=${token}; path=/; SameSite=Strict`;
        set({ token, user, isAuthenticated: true });
      },

      logout: () => {
        localStorage.removeItem("ai_librarian_token");
        localStorage.removeItem("ai_librarian_user");
        // Clear cookie
        document.cookie = "ai_librarian_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    {
      name: "ai-librarian-auth",
      // Only persist these keys
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
