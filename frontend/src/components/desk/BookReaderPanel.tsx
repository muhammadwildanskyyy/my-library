"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  ExternalLink,
  FileText,
  Loader2,
  Table2,
} from "lucide-react";
import { useBookChunks } from "@/hooks/useBooks";
import type { Book, ChunkItem } from "@/types/api";

interface BookReaderPanelProps {
  /** The book being viewed */
  book: Book;
  /** The chunk_index to scroll to and highlight on open */
  highlightChunkIndex?: number;
  /** True if user is resizing the sidebar */
  isDragging?: boolean;
  /** Called when user clicks the back arrow */
  onClose: () => void;
}

export default function BookReaderPanel({
  book,
  highlightChunkIndex,
  isDragging = false,
  onClose,
}: BookReaderPanelProps) {
  const { data, isLoading, isError } = useBookChunks(book.id);
  const [viewMode, setViewMode] = useState<"text" | "pdf">("text");
  const highlightRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Scroll to highlighted chunk whenever it changes or data loads
  const scrollToChunk = useCallback(() => {
    if (highlightRef.current && containerRef.current) {
      highlightRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, []);

  useEffect(() => {
    if (data && highlightChunkIndex !== undefined) {
      // Small delay to let the DOM fully render before scrolling
      const timer = setTimeout(scrollToChunk, 150);
      return () => clearTimeout(timer);
    }
  }, [data, highlightChunkIndex, scrollToChunk]);

  return (
    <div className="h-full bg-parchment border-r border-border/60 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 bg-gradient-to-b from-mahogany to-mahogany/80 text-white">
        {/* Decorative stripe */}
        <div className="h-1 w-full bg-brass/60" />

        {/* Navigation row */}
        <div className="px-4 pt-3 pb-2 flex items-center justify-between gap-2.5">
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 text-white/70 hover:text-white text-xs transition-colors group"
            aria-label="Back to main panel"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back</span>
          </button>

          {book.file_url && (
            <div className="flex bg-black/20 rounded-md p-0.5 ml-auto mr-3">
              <button 
                onClick={() => setViewMode("text")} 
                className={`px-3 py-1 text-[10px] rounded-sm transition-colors ${viewMode === 'text' ? 'bg-brass/90 text-mahogany font-bold shadow-sm' : 'text-white/70 hover:text-white hover:bg-white/10'}`}
              >
                Text
              </button>
              <button 
                onClick={() => setViewMode("pdf")} 
                className={`px-3 py-1 text-[10px] rounded-sm transition-colors ${viewMode === 'pdf' ? 'bg-brass/90 text-mahogany font-bold shadow-sm' : 'text-white/70 hover:text-white hover:bg-white/10'}`}
              >
                PDF
              </button>
            </div>
          )}

          {book.file_url && (
            <a
              href={book.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-white/50 hover:text-white transition-colors"
              title="Open original PDF in a new tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>

        {/* Book title */}
        <div className="px-4 pb-4">
          <div className="flex items-center gap-1.5 text-white/60 text-[10px] mb-1">
            <BookOpen className="w-3 h-3" />
            <span>Text Reader</span>
          </div>
          <h2 className="text-sm font-bold leading-tight line-clamp-2">
            {book.title}
          </h2>
          {highlightChunkIndex !== undefined && (
            <p className="text-white/50 text-[10px] mt-1">
              Showing chunk #{highlightChunkIndex + 1} of {data?.total ?? "..."}
            </p>
          )}
        </div>
      </div>

      {/* Content area */}
      {viewMode === "pdf" && book.file_url ? (
        <iframe 
          src={`https://docs.google.com/viewer?url=${encodeURIComponent(book.file_url)}&embedded=true`} 
          className={`w-full flex-1 border-none bg-white ${isDragging ? "pointer-events-none" : ""}`} 
          title={book.title} 
        />
      ) : (
        <div
          ref={containerRef}
          className="flex-1 overflow-y-auto px-6 py-6 text-justify"
        >
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-40 gap-3 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin text-brass/60" />
              <p className="text-xs">Loading book content...</p>
            </div>
          )}

          {isError && (
            <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg mt-4">
              <p className="text-xs text-red-600 text-center">
                Failed to load book content. Please try again.
              </p>
            </div>
          )}

          {data?.chunks.map((chunk) => {
            const isHighlighted = chunk.chunk_index === highlightChunkIndex;
            return (
              <ChunkBlock
                key={chunk.chunk_index}
                chunk={chunk}
                isHighlighted={isHighlighted}
                ref={isHighlighted ? highlightRef : null}
              />
            );
          })}

          {data && data.chunks.length === 0 && (
            <div className="flex flex-col items-center justify-center h-40 gap-3 text-muted-foreground">
              <BookOpen className="w-8 h-8 text-brass/30" />
              <p className="text-xs text-center">
                This book has no indexed content yet.
              </p>
            </div>
          )}

          {/* Bottom padding */}
          <div className="h-8" />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ChunkBlock — renders a single text/table chunk with highlight support
// ---------------------------------------------------------------------------
interface ChunkBlockProps {
  chunk: ChunkItem;
  isHighlighted: boolean;
  ref?: React.Ref<HTMLDivElement> | null;
}

const ChunkBlock = ({
  chunk,
  isHighlighted,
  ref,
}: ChunkBlockProps) => {
  const isTable = chunk.source_type === "table";

  return (
    <div
      ref={ref}
      id={`chunk-${chunk.chunk_index}`}
      className={[
        "relative text-[13px] leading-relaxed transition-colors duration-700",
        isTable
          ? "font-mono bg-muted/20 border border-border/30 p-3 rounded-md text-[11px] overflow-x-auto my-4 block"
          : "text-foreground/90 inline",
        isHighlighted
          ? "bg-yellow-200/50 dark:bg-yellow-500/30 rounded-sm shadow-[0_0_0_2px_rgba(254,240,138,0.5)] dark:shadow-[0_0_0_2px_rgba(234,179,8,0.3)]"
          : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!isTable && (
        <span className="text-[9px] text-muted-foreground/30 select-none mr-2 font-mono">
          [p.{chunk.page}]
        </span>
      )}
      
      {isTable && (
        <div className="flex items-center gap-1.5 mb-2 text-[9px] text-muted-foreground/50 uppercase tracking-wider">
          <Table2 className="w-2.5 h-2.5" />
          <span>Table · Pg. {chunk.page}</span>
          {isHighlighted && (
            <span className="ml-auto flex items-center gap-1 text-yellow-600 font-semibold">
              <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full animate-pulse" />
              Source
            </span>
          )}
        </div>
      )}

      {/* Content */}
      <span className={isTable ? "whitespace-pre-wrap break-words" : ""}>
        {chunk.content}{" "}
      </span>

      {!isTable && isHighlighted && (
         <span className="inline-flex items-center gap-1 text-[9px] text-yellow-600 font-semibold ml-1 select-none">
           <span className="w-1 h-1 bg-yellow-600 rounded-full animate-pulse" />
           source
         </span>
      )}
    </div>
  );
};
