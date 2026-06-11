/**
 * TanStack Query hooks for Books.
 * Endpoints:
 *  GET   /api/v1/libraries/{library_id}/books/
 *  GET   /api/v1/shelves/{shelf_id}/books/
 *  GET   /api/v1/books/{book_id}
 *  PATCH /api/v1/books/{book_id}/move
 *  DELETE /api/v1/books/{book_id}
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { Book, BookChunksResponse, BookListResponse, BookMoveRequest, BookUpdate } from "@/types/api";

export const bookKeys = {
  all: ["books"] as const,
  byLibrary: (libraryId: string) =>
    [...bookKeys.all, "library", libraryId] as const,
  byShelf: (shelfId: string) =>
    [...bookKeys.all, "shelf", shelfId] as const,
  detail: (bookId: string) => [...bookKeys.all, "detail", bookId] as const,
};

export const chunkKeys = {
  all: ["chunks"] as const,
  byBook: (bookId: string) => [...chunkKeys.all, "book", bookId] as const,
};

// GET /api/v1/libraries/{library_id}/books/
// Returns ALL books in the library (grouped by shelf_id in UI)
export function useBooksByLibrary(libraryId: string | null) {
  return useQuery({
    queryKey: bookKeys.byLibrary(libraryId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<BookListResponse>(
        `/libraries/${libraryId}/books/`
      );
      return data;
    },
    enabled: !!libraryId,
    // Poll every 5s when any book is in "processing" state
    refetchInterval: (query) => {
      const books = query.state.data?.books ?? [];
      return books.some((b) => b.status === "processing") ? 5000 : false;
    },
  });
}

// GET /api/v1/shelves/{shelf_id}/books/
export function useBooksByShelf(shelfId: string | null) {
  return useQuery({
    queryKey: bookKeys.byShelf(shelfId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<BookListResponse>(
        `/shelves/${shelfId}/books/`
      );
      return data;
    },
    enabled: !!shelfId,
  });
}

// GET /api/v1/books/{book_id}
export function useBook(bookId: string | null) {
  return useQuery({
    queryKey: bookKeys.detail(bookId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<Book>(`/books/${bookId}`);
      return data;
    },
    enabled: !!bookId,
  });
}

// PATCH /api/v1/books/{book_id}/move
export function useMoveBook(libraryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      bookId,
      body,
    }: {
      bookId: string;
      body: BookMoveRequest;
    }) => {
      const { data } = await apiClient.patch<Book>(
        `/books/${bookId}/move`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: bookKeys.byLibrary(libraryId),
      });
    },
  });
}

// DELETE /api/v1/books/{book_id}
export function useDeleteBook(libraryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (bookId: string) => {
      await apiClient.delete(`/books/${bookId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: bookKeys.byLibrary(libraryId),
      });
    },
  });
}

// PATCH /api/v1/books/{book_id}
export function useUpdateBook(libraryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      bookId,
      body,
    }: {
      bookId: string;
      body: BookUpdate;
    }) => {
      const { data } = await apiClient.patch<Book>(
        `/books/${bookId}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: bookKeys.byLibrary(libraryId),
      });
    },
  });
}

// GET /api/v1/books/{book_id}/chunks/
export function useBookChunks(bookId: string | null) {
  return useQuery({
    queryKey: chunkKeys.byBook(bookId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<BookChunksResponse>(
        `/books/${bookId}/chunks/`
      );
      return data;
    },
    enabled: !!bookId,
    // Chunks are immutable once ingested — cache aggressively
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}
