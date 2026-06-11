/**
 * TanStack Query hooks for Chat Sessions & Messages.
 *
 * Endpoints (real backend):
 *  POST /api/v1/chat/sessions/                              → create session
 *  GET  /api/v1/chat/sessions/?library_id={id}             → list sessions
 *  POST /api/v1/chat/sessions/{session_id}/messages/        → send message (triggers RAG)
 *  GET  /api/v1/chat/sessions/{session_id}/messages/        → message history
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type {
  ChatHistoryResponse,
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionCreate,
  ChatSessionListResponse,
  ChatSessionUpdate,
} from "@/types/api";

export const chatKeys = {
  all: ["chat"] as const,
  sessions: (libraryId: string, shelfId?: string | null) =>
    [...chatKeys.all, "sessions", libraryId, shelfId ?? "global"] as const,
  history: (sessionId: string) =>
    [...chatKeys.all, "history", sessionId] as const,
};

// POST /api/v1/chat/sessions/
export function useCreateChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ChatSessionCreate) => {
      const { data } = await apiClient.post<ChatSession>(
        "/chat/sessions/",
        body
      );
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: chatKeys.sessions(variables.library_id, variables.shelf_id),
      });
    },
  });
}

// GET /api/v1/chat/sessions/?library_id={library_id}&shelf_id={shelf_id}
export function useChatSessions(libraryId: string | null, shelfId?: string | null) {
  return useQuery({
    queryKey: chatKeys.sessions(libraryId ?? "", shelfId),
    queryFn: async () => {
      const { data } = await apiClient.get<ChatSessionListResponse>(
        "/chat/sessions/",
        { params: { library_id: libraryId, ...(shelfId ? { shelf_id: shelfId } : {}) } }
      );
      return data;
    },
    enabled: !!libraryId,
  });
}

// GET /api/v1/chat/sessions/{session_id}/messages/
export function useChatHistory(sessionId: string | null) {
  return useQuery({
    queryKey: chatKeys.history(sessionId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<ChatHistoryResponse>(
        `/chat/sessions/${sessionId}/messages/`
      );
      return data;
    },
    enabled: !!sessionId,
  });
}

// POST /api/v1/chat/sessions/{session_id}/messages/
export function useSendMessage(sessionId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ChatRequest & { explicitSessionId?: string }) => {
      const targetId = body.explicitSessionId || sessionId;
      if (!targetId) throw new Error("No active chat session");
      
      const { explicitSessionId, ...restBody } = body;
      const { data } = await apiClient.post<ChatResponse>(
        `/chat/sessions/${targetId}/messages/`,
        restBody
      );
      return { data, targetId };
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({
        queryKey: chatKeys.history(result.targetId),
      });
      // Invalidate sessions list as well, in case the backend just generated a new title
      queryClient.invalidateQueries({
        queryKey: ["chat", "sessions"],
      });
    },
  });
}

// PATCH /api/v1/chat/sessions/{session_id}
export function useUpdateChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, body }: { sessionId: string; body: ChatSessionUpdate }) => {
      const { data } = await apiClient.patch<ChatSession>(
        `/chat/sessions/${sessionId}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    },
  });
}

// DELETE /api/v1/chat/sessions/{session_id}
export function useDeleteChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      await apiClient.delete(`/chat/sessions/${sessionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    },
  });
}
