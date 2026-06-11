/**
 * TanStack Query hooks for Book Upload.
 * Endpoint: POST /api/v1/libraries/{library_id}/books/  (multipart/form-data)
 *
 * Form fields:
 *  - file:     PDF UploadFile
 *  - title:    string (Form)
 *  - shelf_id: UUID | null (Form, optional)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { Book } from "@/types/api";
import { bookKeys } from "./useBooks";

export interface UploadBookParams {
  libraryId: string;
  file: File;
  title: string;
  shelfId?: string | null;
}

export function useUploadBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ libraryId, file, title, shelfId }: UploadBookParams) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title);
      if (shelfId) {
        formData.append("shelf_id", shelfId);
      }

      const { data } = await apiClient.post<Book>(
        `/libraries/${libraryId}/books/`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      return data;
    },
    onSuccess: (_data, variables) => {
      // Invalidate library books cache to show newly uploaded book
      queryClient.invalidateQueries({
        queryKey: bookKeys.byLibrary(variables.libraryId),
      });
    },
  });
}
