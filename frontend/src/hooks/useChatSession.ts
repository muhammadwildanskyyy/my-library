/**
 * TanStack Query hooks for Chat Sessions & Messages.
 *
 * Endpoints (real backend):
 *  POST /api/v1/chat/sessions/                              → create session
 *  GET  /api/v1/chat/sessions/?library_id={id}             → list sessions
 *  POST /api/v1/chat/sessions/{session_id}/messages/        → send message (triggers RAG)
 *  POST /api/v1/chat/sessions/{session_id}/messages/stream  → stream message (SSE)
 *  GET  /api/v1/chat/sessions/{session_id}/messages/        → message history
 */

import { useCallback, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import { streamChatMessage, type StreamMetadata } from "@/lib/chatStream";
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

// ---------------------------------------------------------------------------
// POST /api/v1/chat/sessions/{session_id}/messages/stream  (SSE)
// ---------------------------------------------------------------------------
export interface StreamingState {
  /** Text accumulated so far during streaming */
  streamingContent: string;
  /** True while tokens are being received */
  isStreaming: boolean;
  /** True while the retrieval phase runs (before first token) */
  isRetrieving: boolean;
  /** Final metadata received at end of stream */
  streamingMeta: StreamMetadata | null;
  /** Error message if streaming failed */
  streamError: string | null;
}

/**
 * Hook for streaming chat responses via SSE.
 *
 * Returns `send(question, sessionId)` plus streaming state.
 * On completion, invalidates the chat history query so the message
 * is fetched from the server (with full DB-backed data).
 */
export function useStreamMessage(sessionId: string | null) {
  const queryClient = useQueryClient();
  const abortRef = useRef<AbortController | null>(null);

  const [state, setState] = useState<StreamingState>({
    streamingContent: "",
    isStreaming: false,
    isRetrieving: false,
    streamingMeta: null,
    streamError: null,
  });

  const send = useCallback(
    async (question: string, explicitSessionId?: string) => {
      const targetId = explicitSessionId || sessionId;
      if (!targetId) throw new Error("No active chat session");

      // Cancel any in-flight stream
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      // Reset state — enter retrieval phase
      setState({
        streamingContent: "",
        isStreaming: false,
        isRetrieving: true,
        streamingMeta: null,
        streamError: null,
      });

      await streamChatMessage({
        sessionId: targetId,
        question,
        signal: controller.signal,

        onToken: (token) => {
          setState((prev) => ({
            ...prev,
            isRetrieving: false,   // first token marks end of retrieval
            isStreaming: true,
            streamingContent: prev.streamingContent + token,
          }));
        },

        onMetadata: (meta) => {
          setState((prev) => ({
            ...prev,
            streamingMeta: meta,
          }));
        },

        onDone: () => {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            isRetrieving: false,
          }));
          // Refresh history from server
          queryClient.invalidateQueries({
            queryKey: chatKeys.history(targetId),
          });
          // Refresh sessions list (title may have been generated)
          queryClient.invalidateQueries({
            queryKey: ["chat", "sessions"],
          });
        },

        onError: (message) => {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            isRetrieving: false,
            streamError: message,
          }));
        },
      });
    },
    [sessionId, queryClient]
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({
      ...prev,
      isStreaming: false,
      isRetrieving: false,
    }));
  }, []);

  return { send, cancel, ...state };
}

