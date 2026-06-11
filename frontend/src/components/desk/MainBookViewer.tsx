"use client";

import { useState } from "react";
import { BookOpen, FileText, Loader2, Table2 } from "lucide-react";
import { useBookChunks } from "@/hooks/useBooks";
import type { Book, ChunkItem } from "@/types/api";

interface MainBookViewerProps {
  book: Book;
  isDragging?: boolean;
}

export default function MainBookViewer({ book, isDragging = false }: MainBookViewerProps) {
  const { data, isLoading, isError } = useBookChunks(book.id);
  const [viewMode, setViewMode] = useState<"pdf" | "text">("pdf");

  return (
    <div className="flex flex-col h-full bg-background relative">
      {/* Top bar */}
      <div className="flex-shrink-0 h-14 border-b border-border/50 bg-background/80 backdrop-blur-md flex items-center justify-between px-6 z-10">
        <h2 className="text-sm font-semibold text-foreground truncate max-w-lg">
          {book.title}
        </h2>

        {book.file_url && (
          <div className="flex items-center bg-muted/50 p-1 rounded-lg">
            <button
              onClick={() => setViewMode("pdf")}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                viewMode === "pdf"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-4 h-4" />
              PDF View
            </button>
            <button
              onClick={() => setViewMode("text")}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                viewMode === "text"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Text Reader
            </button>
          </div>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 relative bg-zinc-50 dark:bg-zinc-950">
        {viewMode === "pdf" && book.file_url ? (
          <iframe
            src={`https://docs.google.com/viewer?url=${encodeURIComponent(
              book.file_url
            )}&embedded=true`}
            className={`w-full h-full border-none ${
              isDragging ? "pointer-events-none" : ""
            }`}
            title={book.title}
          />
        ) : (
          <div className="w-full h-full overflow-y-auto px-6 py-12">
            <div className="max-w-3xl mx-auto bg-background p-8 sm:p-12 shadow-sm border border-border/40 rounded-xl">
              {isLoading && (
                <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
                  <Loader2 className="w-8 h-8 animate-spin text-brass/60" />
                  <p>Loading document text...</p>
                </div>
              )}

              {isError && (
                <div className="p-6 bg-red-500/5 border border-red-500/20 rounded-lg">
                  <p className="text-red-600 text-center">
                    Failed to load document text. Please try again later.
                  </p>
                </div>
              )}

              <div className="prose prose-zinc dark:prose-invert max-w-none">
                {data?.chunks.map((chunk) => (
                  <ChunkBlock key={chunk.chunk_index} chunk={chunk} />
                ))}
              </div>

              {data && data.chunks.length === 0 && (
                <div className="flex flex-col items-center justify-center h-64 gap-4 text-muted-foreground">
                  <BookOpen className="w-12 h-12 text-brass/30" />
                  <p className="text-center text-lg">
                    This document has no indexed text content.
                  </p>
                </div>
              )}
            </div>
            {/* Bottom padding */}
            <div className="h-16" />
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ChunkBlock
// ---------------------------------------------------------------------------
function ChunkBlock({ chunk }: { chunk: ChunkItem }) {
  const isTable = chunk.source_type === "table";

  return (
    <div
      id={`chunk-${chunk.chunk_index}`}
      className={[
        "relative text-[15px] leading-relaxed",
        isTable
          ? "font-mono bg-muted/30 border border-border/50 p-4 rounded-lg text-xs overflow-x-auto my-6 block whitespace-pre-wrap"
          : "text-foreground inline",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!isTable && (
        <span className="text-[10px] text-muted-foreground/40 select-none mr-2.5 font-mono inline-block transform -translate-y-px">
          [p.{chunk.page}]
        </span>
      )}

      {isTable && (
        <div className="flex items-center gap-1.5 mb-3 text-[10px] text-muted-foreground/60 uppercase tracking-wider font-sans">
          <Table2 className="w-3 h-3" />
          <span>Table · Page {chunk.page}</span>
        </div>
      )}

      {chunk.content}

      {!isTable && <span className="mr-1.5 inline-block" />}
    </div>
  );
}
