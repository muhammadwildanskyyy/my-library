"use client";

import { Bot, User, Globe, BookOpen } from "lucide-react";
import type { ChatMessage, ReferenceItem } from "@/types/api";

interface MessageBubbleProps {
  message: ChatMessage;
  onRefClick?: (ref: ReferenceItem) => void;
}

export default function MessageBubble({ message, onRefClick }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const refs = message.references ?? [];

  return (
    <div
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} items-start`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
          isUser
            ? "bg-mahogany text-white"
            : "bg-brass/20 text-brass border border-brass/30"
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble */}
      <div className={`flex flex-col gap-1.5 max-w-[78%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
            isUser
              ? "bg-mahogany text-white rounded-tr-sm"
              : "bg-card border border-border/50 text-foreground rounded-tl-sm"
          }`}
        >
          {/* Render answer with [N] reference markers highlighted */}
          {isUser ? (
            message.content
          ) : (
            <AnswerWithRefs
              content={message.content}
              refs={refs}
              onRefClick={onRefClick}
            />
          )}
        </div>

        {/* Web fallback badge */}
        {!isUser && message.from_web && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground px-1">
            <Globe className="w-3 h-3" />
            <span>Used web search as fallback</span>
          </div>
        )}

        {/* References chips */}
        {!isUser && refs.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1 mt-1">
            {refs.map((ref) => (
              <ReferenceChip
                key={`${ref.ref_index}-${ref.book_id}`}
                ref_={ref}
                onClick={onRefClick}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-muted-foreground/50 px-1">
          {new Date(message.created_at).toLocaleTimeString("id-ID", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// AnswerWithRefs — renders AI text with clickable [N] superscript markers
// ---------------------------------------------------------------------------
function AnswerWithRefs({
  content,
  refs,
  onRefClick,
}: {
  content: string;
  refs: ReferenceItem[];
  onRefClick?: (ref: ReferenceItem) => void;
}) {
  const parts = content.split(/(\[\d+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        if (/^\[\d+\]$/.test(part)) {
          const idx = parseInt(part.replace(/\[|\]/g, ""), 10);
          const ref = refs.find((r) => r.ref_index === idx);

          if (ref && onRefClick) {
            return (
              <button
                key={i}
                onClick={() => onRefClick(ref)}
                title={`[${idx}] ${ref.book_title} — chunk ${ref.chunk_index}`}
                className="inline-flex items-center justify-center w-4 h-4 text-[9px] font-bold bg-brass/20 text-brass border border-brass/30 rounded-full mx-0.5 cursor-pointer hover:bg-brass/40 hover:border-brass/60 transition-colors"
              >
                {idx}
              </button>
            );
          }

          // Fallback: no handler or ref not found
          return (
            <sup
              key={i}
              className="inline-flex items-center justify-center w-4 h-4 text-[9px] font-bold bg-brass/20 text-brass border border-brass/30 rounded-full mx-0.5 cursor-default"
            >
              {idx}
            </sup>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

// ---------------------------------------------------------------------------
// ReferenceChip — clickable reference pill shown below AI bubble
// ---------------------------------------------------------------------------
function ReferenceChip({
  ref_,
  onClick,
}: {
  ref_: ReferenceItem;
  onClick?: (ref: ReferenceItem) => void;
}) {
  const inner = (
    <>
      <BookOpen className="w-2.5 h-2.5 text-brass/70 flex-shrink-0" />
      <span className="font-medium text-brass/80">[{ref_.ref_index}]</span>
      <span className="truncate max-w-[120px]">{ref_.book_title}</span>
    </>
  );

  if (onClick) {
    return (
      <button
        onClick={() => onClick(ref_)}
        className="inline-flex items-center gap-1.5 text-[11px] bg-aged-paper border border-brass/20 rounded-full px-2.5 py-1 text-muted-foreground hover:border-brass/50 hover:text-foreground hover:bg-brass/10 transition-all cursor-pointer"
        title={`${ref_.book_title} — chunk ${ref_.chunk_index} (${ref_.source_type})`}
      >
        {inner}
      </button>
    );
  }

  return (
    <div
      className="inline-flex items-center gap-1.5 text-[11px] bg-aged-paper border border-brass/20 rounded-full px-2.5 py-1 text-muted-foreground"
      title={`${ref_.book_title} — chunk ${ref_.chunk_index} (${ref_.source_type})`}
    >
      {inner}
    </div>
  );
}
