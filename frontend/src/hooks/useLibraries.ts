/**
 * TanStack Query hooks for Library CRUD.
 * Endpoints:
 *  GET    /api/v1/libraries/
 *  POST   /api/v1/libraries/
 *  DELETE /api/v1/libraries/{library_id}
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type {
  Library,
  LibraryCreate,
  LibraryListResponse,
  LibraryUpdate,
} from "@/types/api";

// Query keys
export const libraryKeys = {
  all: ["libraries"] as const,
  lists: () => [...libraryKeys.all, "list"] as const,
  detail: (id: string) => [...libraryKeys.all, "detail", id] as const,
};

// GET /api/v1/libraries/
export function useLibraries() {
  return useQuery({
    queryKey: libraryKeys.lists(),
    queryFn: async () => {
      const { data } = await apiClient.get<LibraryListResponse>("/libraries/");
      return data;
    },
  });
}

// GET /api/v1/libraries/{library_id}
export function useLibrary(libraryId: string | null) {
  return useQuery({
    queryKey: libraryKeys.detail(libraryId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<Library>(`/libraries/${libraryId}`);
      return data;
    },
    enabled: !!libraryId,
  });
}

// POST /api/v1/libraries/
export function useCreateLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: LibraryCreate) => {
      const { data } = await apiClient.post<Library>("/libraries/", body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: libraryKeys.lists() });
    },
  });
}

// DELETE /api/v1/libraries/{library_id}
export function useDeleteLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (libraryId: string) => {
      await apiClient.delete(`/libraries/${libraryId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: libraryKeys.lists() });
    },
  });
}

// PATCH /api/v1/libraries/{library_id}
export function useUpdateLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      libraryId,
      body,
    }: {
      libraryId: string;
      body: LibraryUpdate;
    }) => {
      const { data } = await apiClient.patch<Library>(
        `/libraries/${libraryId}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: libraryKeys.lists() });
    },
  });
}
