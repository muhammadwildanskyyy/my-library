/**
 * Library Zustand store
 *
 * Notice: View modes (LOBBY, STACKS, DESK) and navigation
 * are now handled by Next.js App Router dynamic routes.
 *
 * This store can be used for any remaining global state (if needed).
 */

import { create } from "zustand";

interface LibraryState {
  // Placeholder for future global state
  _placeholder?: string;
}

export const useLibraryStore = create<LibraryState>(() => ({}));
