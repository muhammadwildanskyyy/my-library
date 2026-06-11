"use client";

/**
 * Deterministic color + visual properties for a book spine
 * derived from the book's UUID.
 */

import type { Book } from "@/types/api";
import { MoreHorizontal, Edit2, Trash2, Check, X } from "lucide-react";
import { useDeleteBook, useUpdateBook } from "@/hooks/useBooks";
import { useParams } from "next/navigation";
import { useState, useMemo, useRef, useEffect } from "react";
import { toast } from "sonner";
import { DeleteBookDialog } from "./DeleteBookDialog";

// Book spine color palette (warm library tones)
const SPINE_COLORS = [
  { bg: "oklch(0.35 0.12 15)",   text: "#f5f0e8", label: "Burgundy" },
  { bg: "oklch(0.35 0.10 150)",  text: "#f5f0e8", label: "Forest" },
  { bg: "oklch(0.30 0.10 250)",  text: "#f5f0e8", label: "Navy" },
  { bg: "oklch(0.55 0.13 75)",   text: "#1a1208", label: "Gold" },
  { bg: "oklch(0.40 0.05 240)",  text: "#f5f0e8", label: "Slate" },
  { bg: "oklch(0.50 0.12 40)",   text: "#f5f0e8", label: "Terracotta" },
  { bg: "oklch(0.55 0.08 145)",  text: "#1a1208", label: "Sage" },
  { bg: "oklch(0.35 0.12 310)",  text: "#f5f0e8", label: "Plum" },
  { bg: "oklch(0.28 0.08 30)",   text: "#f5f0e8", label: "Chocolate" },
  { bg: "oklch(0.42 0.09 200)",  text: "#f5f0e8", label: "Teal" },
];

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
  }
  return hash;
}

// Normalize file_size to a height in px (120px–180px)
function normalizeHeight(fileSize: number): number {
  const MIN_SIZE = 10 * 1024;
  const MAX_SIZE = 10 * 1024 * 1024;
  const MIN_H = 120;
  const MAX_H = 180;
  const clamped = Math.max(MIN_SIZE, Math.min(MAX_SIZE, fileSize));
  return MIN_H + ((clamped - MIN_SIZE) / (MAX_SIZE - MIN_SIZE)) * (MAX_H - MIN_H);
}

// Normalize total_chunks to a width in px (20px–40px)
function normalizeWidth(chunks: number): number {
  const MIN_CHUNKS = 1;
  const MAX_CHUNKS = 50;
  const MIN_W = 20;
  const MAX_W = 40;
  const clamped = Math.max(MIN_CHUNKS, Math.min(MAX_CHUNKS, chunks));
  return MIN_W + ((clamped - MIN_CHUNKS) / (MAX_CHUNKS - MIN_CHUNKS)) * (MAX_W - MIN_W);
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface BookSpineProps {
  book: Book;
  onClick: () => void;
}

export default function BookSpine({ book, onClick }: BookSpineProps) {
  const params = useParams<{ libraryId: string }>();
  const libraryId = params?.libraryId ?? "";
  
  const updateBook = useUpdateBook(libraryId);
  const deleteBook = useDeleteBook(libraryId);

  const [isDragging, setIsDragging] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(book.title);
  const menuRef = useRef<HTMLDivElement>(null);

  const { color, height, width } = useMemo(() => {
    const hash = hashString(book.id);
    const color = SPINE_COLORS[hash % SPINE_COLORS.length];
    const height = normalizeHeight(book.file_size);
    const width = normalizeWidth(book.total_chunks);
    return { color, height, width };
  }, [book.id, book.file_size, book.total_chunks]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isProcessing = book.status === "processing";
  const isFailed = book.status === "failed";

  const handleSave = async () => {
    if (editName.trim() && editName.trim() !== book.title) {
      try {
        await updateBook.mutateAsync({ bookId: book.id, body: { title: editName.trim() } });
        toast.success("Book renamed.");
      } catch {
        toast.error("Failed to rename book.");
        setEditName(book.title);
      }
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditName(book.title);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    try {
      await deleteBook.mutateAsync(book.id);
      toast.success("Book deleted.");
      setShowDeleteDialog(false);
    } catch {
      toast.error("Failed to delete book.");
    }
  };

  return (
    <div
      ref={menuRef}
      draggable
      data-book-id={book.id}
      onDragStart={(e) => {
        if (isEditing) {
          e.preventDefault();
          return;
        }
        e.dataTransfer.setData("application/vnd.book.id", book.id);
        e.dataTransfer.effectAllowed = "move";
        // Use a tiny delay to ensure the browser captures the drag image first
        setTimeout(() => setIsDragging(true), 50);
      }}
      onDragEnd={() => {
        setIsDragging(false);
      }}
      className={`relative group flex-shrink-0 book-appear ${isEditing ? "" : "cursor-grab active:cursor-grabbing"} ${isDragging ? "invisible pointer-events-none" : ""}`}
      style={{ width, height, marginBottom: "4px" }}
      title={`${book.title}\n${formatFileSize(book.file_size)} · ${book.total_chunks} chunks`}
    >
      <button
        onClick={onClick}
        onContextMenu={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setShowMenu(!showMenu);
        }}
        disabled={isProcessing || isFailed || isEditing}
        className="relative w-full h-full rounded-sm overflow-hidden shadow-md hover:shadow-xl transition-all duration-200 hover:-translate-y-2 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-brass disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:scale-100"
        style={{ background: color.bg }}
      >
        {/* Spine texture — subtle gradient */}
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(to right, oklch(0 0 0 / 15%) 0%, transparent 25%, transparent 75%, oklch(0 0 0 / 10%) 100%)`,
          }}
        />

        {/* Top cap */}
        <div
          className="absolute top-0 left-0 right-0 h-2"
          style={{ background: `oklch(from ${color.bg} calc(l + 0.05) c h / 0.9)` }}
        />

        {/* Title — rotated along spine */}
        <div
          className="absolute inset-0 flex items-center justify-center overflow-hidden"
          style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
        >
          <span
            className="text-[10px] font-semibold tracking-widest px-1 leading-tight select-none"
            style={{
              color: color.text,
              transform: "rotate(180deg)",
              maxHeight: `${height - 20}px`,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {book.title}
          </span>
        </div>

        {/* Processing shimmer overlay */}
        {isProcessing && (
          <div className="absolute inset-0 shimmer opacity-60" />
        )}

        {/* Failed indicator */}
        {isFailed && (
          <div className="absolute inset-0 bg-destructive/30 flex items-end justify-center pb-2">
            <span className="text-[8px] text-white font-bold">ERR</span>
          </div>
        )}

        {/* Status dot */}
        <div className="absolute bottom-1 left-1/2 -translate-x-1/2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              book.status === "ready"
                ? "bg-green-400"
                : book.status === "processing"
                ? "bg-yellow-400 animate-pulse"
                : "bg-red-400"
            }`}
          />
        </div>
      </button>



      {/* Popover Menu */}
      {showMenu && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 w-32 bg-popover border border-border/60 rounded-md shadow-xl z-50 flex flex-col overflow-hidden">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(false);
              setEditName(book.title);
              setIsEditing(true);
            }}
            className="flex items-center gap-2 px-3 py-2 text-xs text-foreground hover:bg-muted transition-colors w-full text-left"
          >
            <Edit2 className="w-3 h-3" />
            Rename
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(false);
              setShowDeleteDialog(true);
            }}
            className="flex items-center gap-2 px-3 py-2 text-xs text-rose-600 hover:bg-rose-500/10 transition-colors w-full text-left border-t border-border/40"
          >
            <Trash2 className="w-3 h-3" />
            Delete
          </button>
        </div>
      )}

      {/* Inline Edit Input Overlay */}
      {isEditing && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-popover/95 backdrop-blur-sm p-1.5 rounded shadow-2xl flex items-center gap-1 border border-border/60 min-w-[140px]">
          <input
            autoFocus
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={(e) => {
              e.stopPropagation();
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") handleCancel();
            }}
            onClick={(e) => e.stopPropagation()}
            className="text-xs bg-transparent border-b border-brass/50 font-semibold text-foreground tracking-wide outline-none focus:border-brass px-1 w-full"
          />
          <button onClick={(e) => { e.stopPropagation(); handleSave(); }} className="p-1 hover:bg-black/5 rounded text-emerald-600">
            <Check className="w-3 h-3" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); handleCancel(); }} className="p-1 hover:bg-black/5 rounded text-rose-600">
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Tooltip on hover */}
      {!showMenu && !isEditing && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 hidden group-hover:block z-30 pointer-events-none">
          <div className="bg-ink/95 text-parchment text-xs rounded-lg px-3 py-2 shadow-xl min-w-max max-w-48 text-center">
            <div className="font-semibold mb-0.5 leading-tight">{book.title}</div>
            <div className="text-parchment/60">
              {formatFileSize(book.file_size)} · {book.total_chunks} chunks
            </div>
            {isProcessing && (
              <div className="text-yellow-400 mt-1">Indexing…</div>
            )}
            {isFailed && (
              <div className="text-red-400 mt-1">Ingestion failed</div>
            )}
            {/* Arrow */}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-ink/95" />
          </div>
        </div>
      )}

      <DeleteBookDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={handleDelete}
        isDeleting={deleteBook.isPending}
        bookName={book.title}
      />
    </div>
  );
}
