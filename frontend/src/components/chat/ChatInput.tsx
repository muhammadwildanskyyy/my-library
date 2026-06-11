"use client";

import {
  useRef,
  useState,
  useCallback,
  KeyboardEvent,
  useEffect,
} from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  isLoading,
  disabled = false,
  placeholder = "Ask the Librarian anything…",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-expand textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setValue("");
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, isLoading, disabled, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter → send
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 border-t border-border/60 bg-card/80 backdrop-blur-sm">
      <div
        className={`flex items-end gap-3 rounded-2xl border-2 transition-colors px-4 py-3 ${
          disabled
            ? "border-border/40 bg-muted/30 opacity-60"
            : "border-border/60 bg-background focus-within:border-brass/50 focus-within:shadow-sm"
        }`}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={placeholder}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground/60 outline-none min-h-[24px] max-h-40 leading-relaxed"
        />

        <Button
          size="sm"
          onClick={handleSend}
          disabled={!value.trim() || isLoading || disabled}
          className="flex-shrink-0 h-8 w-8 p-0 rounded-xl bg-mahogany hover:bg-mahogany-light text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
        </Button>
      </div>

      <p className="text-[10px] text-muted-foreground/40 text-center mt-2">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}
