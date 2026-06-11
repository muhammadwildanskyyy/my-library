/**
 * Axios instance with JWT auth interceptor.
 * Reads token from useAuthStore and injects Authorization header.
 */

import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — inject JWT token
apiClient.interceptors.request.use((config) => {
  // Import lazily to avoid circular dependency with the store
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("ai_librarian_token")
      : null;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      // Clear stored token and redirect to login
      localStorage.removeItem("ai_librarian_token");
      localStorage.removeItem("ai_librarian_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
