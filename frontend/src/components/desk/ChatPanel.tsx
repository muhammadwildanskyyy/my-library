"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Bot, Library, Layers, Info, AlertCircle } from "lucide-react";
import { useSearchParams } from "next/navigation";
import {
  useCreateChatSession,
  useChatHistory,
  useStreamMessage,
} from "@/hooks/useChatSession";
import { toast } from "sonner";
import type { Book, ChatMessage, ReferenceItem } from "@/types/api";

import MessageBubble from "@/components/chat/MessageBubble";
import StreamingBubble from "@/components/chat/StreamingBubble";
import ChatInput from "@/components/chat/ChatInput";

/** Optimistic user message shown instantly before server confirms */
interface OptimisticUserMessage {
  id: string;
  role: "user";
  content: string;
  from_web: boolean;
  token_count: number;
  created_at: string;
  session_id: string;
  references: ReferenceItem[];
}

interface ChatPanelProps {
  libraryId: string;
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  onRefClick?: (ref: ReferenceItem) => void;
}

export default function ChatPanel({
  libraryId: activeLibraryId,
  sessionId,
  setSessionId,
  onRefClick,
}: ChatPanelProps) {
  const searchParams = useSearchParams();
  const activeShelfId = searchParams.get("shelfId");

  // Optimistic user messages for instant feedback
  const [optimisticUserMessages, setOptimisticUserMessages] = useState<
    OptimisticUserMessage[]
  >([]);

  // Chat scope: library-wide (false) or shelf-scoped (true)
  const [shelfScoped, setShelfScoped] = useState(!!activeShelfId);

  // Sync scope when navigating between routes
  useEffect(() => {
    setShelfScoped(!!activeShelfId);
  }, [activeShelfId]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const createSession = useCreateChatSession();
  const { data: historyData } = useChatHistory(sessionId);

  // Streaming state
  const {
    send: streamSend,
    isStreaming,
    isRetrieving,
    streamingContent,
    streamingMeta,
    streamError,
  } = useStreamMessage(sessionId);

  // ── Bug fixes ──────────────────────────────────────────────────────────────
  //
  // Bug 1: The optimistic user message was cleared whenever historyData
  //        changed — including the initial empty fetch ({messages:[]}), so
  //        the user's question disappeared before the AI responded.
  //        Fix: only clear optimistic messages when history actually contains
  //        real messages (the server persisted them).
  //
  // Bug 2: After streaming finishes (isStreaming→false) the StreamingBubble
  //        disappears immediately, but the history refetch takes ~200–400 ms.
  //        During that gap nothing renders, then MessageBubble pops in with
  //        a different layout (AnswerWithRefs) — causing a visible layout jump.
  //        Fix: track `pendingStreamContent` — keep the final streamed text
  //        visible in a static StreamingBubble until the history reload
  //        actually delivers the new message.
  //
  const [pendingStreamContent, setPendingStreamContent] = useState<string>("");
  const serverMessageCountRef = useRef<number>(0);

  // Detect streaming finished: capture final content → enter "pending sync" phase
  const prevIsStreamingRef = useRef(false);
  useEffect(() => {
    const wasStreaming = prevIsStreamingRef.current;
    prevIsStreamingRef.current = isStreaming;

    if (wasStreaming && !isStreaming && streamingContent) {
      // Streaming just ended — preserve the content until history arrives
      setPendingStreamContent(streamingContent);
    }
  }, [isStreaming, streamingContent]);

  // When history loads with new messages: clear optimistic messages AND
  // the pending stream placeholder (Bug 1 + Bug 2 fix)
  useEffect(() => {
    const count = historyData?.messages.length ?? 0;
    if (count > 0 && count > serverMessageCountRef.current) {
      serverMessageCountRef.current = count;
      setOptimisticUserMessages([]);
      setPendingStreamContent("");
    }
  }, [historyData]);

  // ──────────────────────────────────────────────────────────────────────────

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [
    historyData,
    optimisticUserMessages,
    streamingContent,
    pendingStreamContent,
    scrollToBottom,
  ]);

  // When scope changes, reset chat
  async function handleScopeChange(toShelf: boolean) {
    if (toShelf && !activeShelfId) return;
    setShelfScoped(toShelf);
    setSessionId(null);
    setOptimisticUserMessages([]);
    setPendingStreamContent("");
    serverMessageCountRef.current = 0;
  }

  // Show stream errors as toasts
  useEffect(() => {
    if (streamError) {
      toast.error("Failed to get AI response: " + streamError);
    }
  }, [streamError]);

  // Handle send message
  async function handleSend(content: string) {
    if (!content.trim() || !activeLibraryId) return;

    // 1. Ensure session exists
    let targetSessionId = sessionId;
    if (!targetSessionId) {
      try {
        const session = await createSession.mutateAsync({
          library_id: activeLibraryId,
          shelf_id: shelfScoped ? activeShelfId : null,
        });
        targetSessionId = session.id;
        setSessionId(session.id);
      } catch {
        toast.error("Failed to create new chat session.");
        return;
      }
    }

    // 2. Show optimistic user message immediately
    const userMsgId = `opt-${crypto.randomUUID()}`;
    const userMsg: OptimisticUserMessage = {
      id: userMsgId,
      role: "user",
      content,
      from_web: false,
      token_count: 0,
      created_at: new Date().toISOString(),
      session_id: targetSessionId,
      references: [],
    };
    setOptimisticUserMessages((prev) => [...prev, userMsg]);

    // 3. Start streaming
    try {
      await streamSend(content, targetSessionId);
    } catch (err) {
      console.error("Stream send failed:", err);
      toast.error("Failed to send message");
      setOptimisticUserMessages((prev) =>
        prev.filter((m) => m.id !== userMsgId)
      );
    }
  }

  const serverMessages: ChatMessage[] = historyData?.messages ?? [];
  const isBusy = isStreaming || isRetrieving || createSession.isPending;
  // Show streaming UI when actively streaming OR while waiting for history sync
  const showStreamingBubble =
    isRetrieving || isStreaming || !!pendingStreamContent;
  const bubbleContent = isStreaming ? streamingContent : pendingStreamContent;


  return (
    <div className="h-full flex flex-col bg-background">
      {/* Chat header */}
      <div className="px-5 py-4 border-b border-border/60 bg-card/50 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
              isBusy
                ? "bg-brass/30 border border-brass/50"
                : "bg-brass/15 border border-brass/30"
            }`}
          >
            <Bot
              className={`w-4 h-4 transition-colors ${
                isBusy ? "text-brass animate-pulse" : "text-brass"
              }`}
            />
          </div>
          <div>
            <div className="text-sm font-semibold text-foreground">
              AI Librarian
            </div>
            <div className="text-[10px] text-muted-foreground">
              {isRetrieving
                ? "Searching knowledge base…"
                : isStreaming
                ? "Writing response…"
                : sessionId
                ? "Session active"
                : "Waiting for new chat"}
            </div>
          </div>
        </div>

        {/* Scope toggle — only show if there's an active shelf */}
        {activeShelfId && (
          <div className="flex items-center gap-1 bg-muted/50 rounded-xl p-1 text-xs">
            <button
              onClick={() => !shelfScoped && handleScopeChange(false)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                !shelfScoped
                  ? "bg-background text-foreground shadow-sm font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Library className="w-3 h-3" />
              Library
            </button>
            <button
              onClick={() => shelfScoped && handleScopeChange(true)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                shelfScoped
                  ? "bg-background text-foreground shadow-sm font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="w-3 h-3" />
              Shelf
            </button>
          </div>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5">
        {/* Empty state */}
        {serverMessages.length === 0 &&
          optimisticUserMessages.length === 0 &&
          !isRetrieving &&
          !isStreaming &&
          !pendingStreamContent && (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
              <div className="w-16 h-16 rounded-full bg-brass/10 border border-brass/20 flex items-center justify-center">
                <Bot className="w-8 h-8 text-brass/70" />
              </div>
              <div>
                <p className="font-semibold text-foreground">
                  {sessionId ? "Ask the Librarian" : "Welcome to Chat"}
                </p>
                <p className="text-sm text-muted-foreground mt-1 max-w-60 leading-relaxed">
                  Feel free to ask a question, a chat session will be created
                  automatically.
                </p>
              </div>
            </div>
          )}

        {/* Render server history */}
        {serverMessages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} onRefClick={onRefClick} />
        ))}

        {/* Optimistic user message — shown while waiting for server */}
        {optimisticUserMessages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg as unknown as ChatMessage}
            onRefClick={onRefClick}
          />
        ))}

        {/* Live streaming bubble — shown during retrieval, streaming, and
            while waiting for history to sync after streaming ends */}
        {showStreamingBubble && (
          <StreamingBubble
            content={bubbleContent}
            isRetrieving={isRetrieving && !streamingContent}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Stats bar (shows last stream metadata) */}
      {streamingMeta && !isBusy && (
        <div className="px-5 py-1.5 bg-muted/30 border-t border-border/40 flex items-center gap-4 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Info className="w-3 h-3" />
            {streamingMeta.num_docs_retrieved} docs retrieved
          </span>
          <span>{streamingMeta.num_docs_relevant} relevant</span>
          {streamingMeta.used_web && (
            <span className="text-yellow-600">+ web search</span>
          )}
        </div>
      )}

      <ChatInput
        onSend={handleSend}
        isLoading={isBusy}
        placeholder="Send your first message..."
      />
    </div>
  );
}
