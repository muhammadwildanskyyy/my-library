/**
 * chatStream.ts
 *
 * Utility for consuming the SSE streaming chat endpoint.
 * Uses native fetch() + ReadableStream — no EventSource (which doesn't support POST).
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export interface StreamMetadata {
  session_id: string;
  message_id: string;
  used_web: boolean;
  num_docs_retrieved: number;
  num_docs_relevant: number;
  references: Array<{
    ref_index: number;
    book_id: string;
    book_title: string;
    filename: string;
    chunk_index: number;
    source_type: string;
  }>;
}

export interface StreamChatOptions {
  sessionId: string;
  question: string;
  onToken: (token: string) => void;
  onMetadata: (meta: StreamMetadata) => void;
  onDone: () => void;
  onError: (message: string) => void;
  signal?: AbortSignal;
}

/**
 * Stream a chat message via Server-Sent Events.
 *
 * Calls ``POST /chat/sessions/{sessionId}/messages/stream``
 * and dispatches callbacks for each event type.
 */
export async function streamChatMessage(opts: StreamChatOptions): Promise<void> {
  const { sessionId, question, onToken, onMetadata, onDone, onError, signal } =
    opts;

  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("ai_librarian_token")
      : null;

  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/chat/sessions/${sessionId}/messages/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question }),
        signal,
      }
    );
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    onError("Network error: failed to connect to stream");
    return;
  }

  if (!response.ok) {
    // Handle 401 — clear token and redirect
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("ai_librarian_token");
      localStorage.removeItem("ai_librarian_user");
      window.location.href = "/login";
      return;
    }
    onError(`Server error: ${response.status} ${response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError("Stream reader not available");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE lines — each event ends with \n\n
      const events = buffer.split("\n\n");
      // Keep the last (possibly incomplete) chunk in the buffer
      buffer = events.pop() ?? "";

      for (const event of events) {
        const dataLine = event
          .split("\n")
          .find((line) => line.startsWith("data: "));
        if (!dataLine) continue;

        const jsonStr = dataLine.slice(6); // strip "data: "
        let parsed: Record<string, unknown>;
        try {
          parsed = JSON.parse(jsonStr);
        } catch {
          continue; // skip malformed events
        }

        const type = parsed.type as string;

        if (type === "token") {
          onToken(parsed.content as string);
        } else if (type === "metadata") {
          onMetadata(parsed as unknown as StreamMetadata);
        } else if (type === "done") {
          onDone();
          return;
        } else if (type === "error") {
          onError(parsed.message as string);
          return;
        }
      }
    }
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    onError("Stream read error: " + (err as Error).message);
  } finally {
    reader.releaseLock();
  }
}
