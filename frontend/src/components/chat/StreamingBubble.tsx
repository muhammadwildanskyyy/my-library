"use client";

import { Bot } from "lucide-react";
import { useEffect, useRef } from "react";

interface StreamingBubbleProps {
  /** Text accumulated so far */
  content: string;
  /** True while retrieval is running (before first token) */
  isRetrieving?: boolean;
}

/**
 * Streaming message bubble.
 *
 * Shows a "thinking" animation during the retrieval phase, then
 * displays tokens character-by-character with an animated cursor.
 */
export default function StreamingBubble({
  content,
  isRetrieving = false,
}: StreamingBubbleProps) {
  const endRef = useRef<HTMLDivElement>(null);

  // Scroll into view as tokens arrive
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [content]);

  return (
    <div className="flex gap-3 flex-row items-start">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brass/20 text-brass border border-brass/30 flex items-center justify-center shadow-sm">
        <Bot className="w-4 h-4" />
      </div>

      {/* Bubble */}
      <div className="flex flex-col gap-1.5 max-w-[78%] items-start">
        <div className="rounded-2xl rounded-tl-sm bg-card border border-border/50 px-4 py-3 text-sm leading-relaxed shadow-sm text-foreground min-w-[80px]">
          {isRetrieving && !content ? (
            /* Retrieval phase — animated dots */
            <ThinkingDots />
          ) : (
            /* Streaming phase — accumulated text + blinking cursor */
            <StreamingText content={content} />
          )}
        </div>
        <div ref={endRef} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ThinkingDots — bouncing dots shown during retrieval
// ---------------------------------------------------------------------------
function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 py-0.5">
      <span
        className="w-1.5 h-1.5 bg-brass/60 rounded-full animate-bounce"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="w-1.5 h-1.5 bg-brass/60 rounded-full animate-bounce"
        style={{ animationDelay: "150ms" }}
      />
      <span
        className="w-1.5 h-1.5 bg-brass/60 rounded-full animate-bounce"
        style={{ animationDelay: "300ms" }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// StreamingText — renders accumulated tokens with a blinking cursor
// ---------------------------------------------------------------------------
function StreamingText({ content }: { content: string }) {
  return (
    <span className="whitespace-pre-wrap break-words">
      {content}
      <span
        className="inline-block w-[2px] h-[1em] bg-brass/70 ml-[2px] align-text-bottom animate-[blink_1s_step-end_infinite]"
        aria-hidden="true"
      />
    </span>
  );
}
