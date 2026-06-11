/**
 * TanStack Query hooks for Shelf CRUD.
 * Endpoints:
 *  GET    /api/v1/libraries/{library_id}/shelves/
 *  POST   /api/v1/libraries/{library_id}/shelves/
 *  DELETE /api/v1/libraries/{library_id}/shelves/{shelf_id}
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { Shelf, ShelfCreate, ShelfListResponse, ShelfUpdate } from "@/types/api";

export const shelfKeys = {
  all: ["shelves"] as const,
  byLibrary: (libraryId: string) => [...shelfKeys.all, libraryId] as const,
  detail: (libraryId: string, shelfId: string) =>
    [...shelfKeys.byLibrary(libraryId), shelfId] as const,
};

// GET /api/v1/libraries/{library_id}/shelves/
export function useShelves(libraryId: string | null) {
  return useQuery({
    queryKey: shelfKeys.byLibrary(libraryId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<ShelfListResponse>(
        `/libraries/${libraryId}/shelves/`
      );
      return data;
    },
    enabled: !!libraryId,
  });
}

// GET /api/v1/libraries/{library_id}/shelves/{shelf_id}
export function useShelf(libraryId: string | null, shelfId: string | null) {
  return useQuery({
    queryKey: shelfKeys.detail(libraryId ?? "", shelfId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<Shelf>(
        `/libraries/${libraryId}/shelves/${shelfId}`
      );
      return data;
    },
    enabled: !!libraryId && !!shelfId,
  });
}

// POST /api/v1/libraries/{library_id}/shelves/
export function useCreateShelf(libraryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ShelfCreate) => {
      const { data } = await apiClient.post<Shelf>(
        `/libraries/${libraryId}/shelves/`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: shelfKeys.byLibrary(libraryId),
      });
    },
  });
}

// DELETE /api/v1/libraries/{library_id}/shelves/{shelf_id}
export function useDeleteShelf(libraryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (shelfId: string) => {
      await apiClient.delete(`/libraries/${libraryId}/shelves/${shelfId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: shelfKeys.byLibrary(libraryId),
      });
    },
  });
}

// PATCH /api/v1/libraries/{library_id}/shelves/{shelf_id}
export function useUpdateShelf(libraryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      shelfId,
      body,
    }: {
      shelfId: string;
      body: ShelfUpdate;
    }) => {
      const { data } = await apiClient.patch<Shelf>(
        `/libraries/${libraryId}/shelves/${shelfId}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: shelfKeys.byLibrary(libraryId),
      });
    },
  });
}
