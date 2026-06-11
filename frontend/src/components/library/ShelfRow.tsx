"use client";

import type { Shelf, Book } from "@/types/api";
import BookSpine from "./BookSpine";
import ShelfPlank from "./ShelfPlank";
import { Plus, Layers, Bot, Edit2, Check, X, MoreVertical, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useUpdateShelf, useDeleteShelf } from "@/hooks/useShelves";
import { useMoveBook } from "@/hooks/useBooks";
import { toast } from "sonner";

interface ShelfRowProps {
  libraryId: string;
  shelf: Shelf | null; // null = "Unshelved" row
  books: Book[];
  onAddBook?: () => void;
}

export default function ShelfRow({ libraryId, shelf, books, onAddBook }: ShelfRowProps) {
  const router = useRouter();
  const updateShelf = useUpdateShelf(libraryId);
  const deleteShelf = useDeleteShelf(libraryId);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(shelf?.name ?? "");
  const [showMenu, setShowMenu] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const moveBook = useMoveBook(libraryId);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSave = async () => {
    if (!shelf) return;
    if (editName.trim() && editName.trim() !== shelf.name) {
      try {
        await updateShelf.mutateAsync({ shelfId: shelf.id, body: { name: editName.trim() } });
        toast.success("Shelf renamed.");
      } catch {
        toast.error("Failed to rename shelf.");
        setEditName(shelf.name);
      }
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    if (shelf) setEditName(shelf.name);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (!shelf) return;
    if (confirm(`Are you sure you want to delete shelf "${shelf.name}"?`)) {
      try {
        await deleteShelf.mutateAsync(shelf.id);
        toast.success("Shelf deleted.");
      } catch {
        toast.error("Failed to delete shelf.");
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    if (e.dataTransfer.types.includes("application/vnd.book.id")) {
      e.preventDefault();
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // We only want to set isDragOver false if we actually leave the container, 
    // but simple leave is usually fine for a basic glow
    setIsDragOver(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const bookId = e.dataTransfer.getData("application/vnd.book.id");
    if (!bookId) return;

    // Skip if already in this shelf
    if (books.some(b => b.id === bookId)) return;

    try {
      await moveBook.mutateAsync({ bookId, body: { shelf_id: shelf ? shelf.id : null } });
      // Toast isn't strictly necessary since it happens fast, but good for feedback
    } catch {
      toast.error("Failed to move book.");
    }
  };

  return (
    <div className="mb-10">
      {/* Shelf label */}
      <div className="flex items-center gap-3 mb-3 px-2">
        <Layers className="w-4 h-4 text-brass/70 flex-shrink-0" />
        {shelf ? (
          isEditing ? (
            <div className="flex items-center gap-1">
              <input
                autoFocus
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSave();
                  if (e.key === "Escape") handleCancel();
                }}
                className="bg-transparent border-b border-brass/50 text-sm font-semibold text-foreground tracking-wide uppercase outline-none focus:border-brass px-1"
              />
              <button onClick={handleSave} className="p-1 hover:bg-black/5 rounded text-emerald-600 dark:text-emerald-400">
                <Check className="w-3.5 h-3.5" />
              </button>
              <button onClick={handleCancel} className="p-1 hover:bg-black/5 rounded text-rose-600 dark:text-rose-400">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1 group/shelfname relative" ref={menuRef}>
              <button
                onClick={() => router.push(`/library/${libraryId}/shelf/${shelf.id}`)}
                className="text-sm font-semibold text-muted-foreground hover:text-foreground tracking-wide uppercase transition-colors"
              >
                {shelf.name}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  setShowMenu(!showMenu);
                }}
                className="relative z-10 flex-shrink-0 p-1 text-muted-foreground hover:text-brass transition-colors rounded"
              >
                <MoreVertical className="w-3.5 h-3.5" />
              </button>

              {showMenu && (
                <div className="absolute left-full ml-1 top-0 w-32 bg-popover border border-border/60 rounded-md shadow-md overflow-hidden z-20 flex flex-col">
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      setEditName(shelf.name);
                      setIsEditing(true);
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs text-foreground hover:bg-muted transition-colors w-full text-left"
                  >
                    <Edit2 className="w-3 h-3" />
                    Rename
                  </button>
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      handleDelete();
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs text-rose-600 hover:bg-rose-500/10 transition-colors w-full text-left border-t border-border/40"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
                  </button>
                </div>
              )}
            </div>
          )
        ) : (
          <span className="text-sm font-semibold text-muted-foreground tracking-wide uppercase">
            Unshelved
          </span>
        )}
        {shelf?.description && (
          <span className="text-xs text-muted-foreground/60 font-normal hidden sm:block">
            — {shelf.description}
          </span>
        )}
        <div className="flex-1 h-px bg-border/40 ml-2" />
        <span className="text-xs text-muted-foreground/50 flex-shrink-0">
          {books.length} {books.length === 1 ? "book" : "books"}
        </span>
      </div>

      {/* Shelf surface with book spines */}
      <ShelfPlank
        books={books}
        emptyMessage="Empty shelf"
        isDragOver={isDragOver}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onBookClick={(book) => {
          const url = `/library/${libraryId}/book/${book.id}${shelf ? `?shelfId=${shelf.id}` : ""}`;
          router.push(url);
        }}
      />

      {/* Action buttons below shelf */}
      <div className="mt-3 ml-2 flex items-center gap-6">
        {onAddBook && (
          <button
            onClick={onAddBook}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-brass transition-colors group"
          >
            <Plus className="w-3.5 h-3.5 group-hover:rotate-90 transition-transform duration-200" />
            Add book to this shelf
          </button>
        )}
        {shelf && (
          <>
            <button
              onClick={() => router.push(`/library/${libraryId}/desk?shelfId=${shelf.id}`)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-brass transition-colors group"
            >
              <Bot className="w-3.5 h-3.5 group-hover:scale-110 transition-transform duration-200" />
              Ask Librarian about this shelf
            </button>
            <button
              onClick={() => router.push(`/library/${libraryId}/shelf/${shelf.id}`)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-brass transition-colors group"
            >
              <Layers className="w-3.5 h-3.5 group-hover:scale-110 transition-transform duration-200" />
              Open Shelf
            </button>
          </>
        )}
      </div>
    </div>
  );
}
