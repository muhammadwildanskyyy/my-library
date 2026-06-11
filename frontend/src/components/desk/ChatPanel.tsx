"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Bot, Library, Layers, Info } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useCreateChatSession, useChatHistory, useSendMessage } from "@/hooks/useChatSession";
import { toast } from "sonner";
import type { Book, ChatMessage, ReferenceItem } from "@/types/api";

import MessageBubble from "@/components/chat/MessageBubble";
import ChatInput from "@/components/chat/ChatInput";

/** Optimistic message shown in the UI while waiting for AI response */
interface OptimisticMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  from_web: boolean;
  token_count: number;
  created_at: string;
  session_id: string;
}

interface ChatPanelProps {
  libraryId: string;
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  onRefClick?: (ref: ReferenceItem) => void;
}

export default function ChatPanel({ libraryId: activeLibraryId, sessionId, setSessionId, onRefClick }: ChatPanelProps) {
  const searchParams = useSearchParams();
  const activeShelfId = searchParams.get("shelfId");

  // Optimistic messages for instant feedback
  const [optimisticMessages, setOptimisticMessages] = useState<OptimisticMessage[]>([]);

  // Chat scope: library-wide (false) or shelf-scoped (true)
  const [shelfScoped, setShelfScoped] = useState(!!activeShelfId);

  // Sync scope when navigating between routes
  useEffect(() => {
    setShelfScoped(!!activeShelfId);
  }, [activeShelfId]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const createSession = useCreateChatSession();
  const { data: historyData } = useChatHistory(sessionId);
  const sendMessage = useSendMessage(sessionId);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [historyData, optimisticMessages, scrollToBottom]);

  // When scope changes, switch to a new chat (no session selected)
  async function handleScopeChange(toShelf: boolean) {
    if (toShelf && !activeShelfId) return;
    setShelfScoped(toShelf);
    setSessionId(null);
    setOptimisticMessages([]);
  }

  // Handle send message
  async function handleSend(content: string) {
    if (!content.trim() || !activeLibraryId) return;

    // 1. Ensure we have an active session ID before sending
    let targetSessionId = sessionId;
    if (!targetSessionId) {
      try {
        const session = await createSession.mutateAsync({
          library_id: activeLibraryId,
          shelf_id: shelfScoped ? activeShelfId : null,
        });
        targetSessionId = session.id;
        setSessionId(session.id);
      } catch (error) {
        toast.error("Failed to create new chat session.");
        return;
      }
    }

    // 2. Add optimistic user message to UI
    const userMsgId = crypto.randomUUID();
    const userMsg: OptimisticMessage = {
      id: userMsgId,
      role: "user",
      content,
      from_web: false,
      token_count: 0,
      created_at: new Date().toISOString(),
      session_id: targetSessionId,
    };
    setOptimisticMessages((prev) => [...prev, userMsg]);

    // 3. Send to API
    try {
      await sendMessage.mutateAsync({
        question: content,
        explicitSessionId: targetSessionId,
      });
    } catch (err) {
      console.error("Chat error:", err);
      toast.error("Failed to send message");
      setOptimisticMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    }
  }

  // Combine history + optimistic messages (history from server is ground truth)
  const serverMessages: ChatMessage[] = historyData?.messages ?? [];

  // Clear optimistic messages whenever the server history successfully syncs/updates
  useEffect(() => {
    setOptimisticMessages([]);
  }, [historyData]);

  // Map session_id → references from the last response
  // (kept for the optimistic assistant placeholder — real refs come from history)
  const [lastRefs, setLastRefs] = useState<ReferenceItem[]>([]);
  useEffect(() => {
    if (sendMessage.data?.data?.references) {
      setLastRefs(sendMessage.data.data.references);
    }
  }, [sendMessage.data]);


  return (
    <div className="h-full flex flex-col bg-background">
      {/* Chat header */}
      <div className="px-5 py-4 border-b border-border/60 bg-card/50 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-brass/15 border border-brass/30 flex items-center justify-center">
            <Bot className="w-4 h-4 text-brass" />
          </div>
          <div>
            <div className="text-sm font-semibold text-foreground">AI Librarian</div>
            <div className="text-[10px] text-muted-foreground">
              {sessionId ? "Session active" : "Waiting for new chat"}
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
        {serverMessages.length === 0 && optimisticMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="w-16 h-16 rounded-full bg-brass/10 border border-brass/20 flex items-center justify-center">
              <Bot className="w-8 h-8 text-brass/70" />
            </div>
            <div>
              <p className="font-semibold text-foreground">
                {sessionId ? "Ask the Librarian" : "Welcome to Chat"}
              </p>
              <p className="text-sm text-muted-foreground mt-1 max-w-60 leading-relaxed">
                Feel free to ask a question, a chat session will be created automatically.
              </p>
            </div>
          </div>
        )}

        {/* Render server history */}
        {serverMessages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onRefClick={onRefClick}
          />
        ))}

        {/* Optimistic messages (shown while waiting for server to sync) */}
        {optimisticMessages
          .filter((m) => m.id.startsWith("opt-") || m.role === "user")
          .slice(-2)
          .map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg as unknown as ChatMessage}
              onRefClick={onRefClick}
            />
          ))}


        {/* Thinking indicator */}
        {sendMessage.isPending && (
          <div className="flex gap-3 items-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brass/20 border border-brass/30 flex items-center justify-center">
              <Bot className="w-4 h-4 text-brass" />
            </div>
            <div className="rounded-2xl rounded-tl-sm bg-card border border-border/50 px-4 py-3 flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-brass/60 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-brass/60 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-brass/60 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Stats bar (when AI responded) */}
      {sendMessage.data && (
        <div className="px-5 py-1.5 bg-muted/30 border-t border-border/40 flex items-center gap-4 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Info className="w-3 h-3" />
            {sendMessage.data.data.num_docs_retrieved} docs retrieved
          </span>
          <span>{sendMessage.data.data.num_docs_relevant} relevant</span>
          {sendMessage.data.data.used_web && (
            <span className="text-yellow-600">+ web search</span>
          )}
        </div>
      )}

      <ChatInput
        onSend={handleSend}
        isLoading={sendMessage.isPending || createSession.isPending}
        placeholder="Send your first message..."
      />
    </div>
  );
}
