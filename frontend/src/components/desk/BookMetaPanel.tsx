"use client";

import { useState, useRef, useEffect } from "react";
import { BookOpen, HardDrive, Layers, Hash, Clock, CheckCircle, AlertCircle, Loader2, Edit2, Check, X, MoreVertical, Trash2, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Book } from "@/types/api";
import { useUpdateBook, useDeleteBook, useMoveBook } from "@/hooks/useBooks";
import { useShelves } from "@/hooks/useShelves";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { DeleteBookDialog } from "../library/DeleteBookDialog";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }: { status: Book["status"] }) {
  if (status === "ready") {
    return (
      <Badge className="bg-green-500/10 text-green-600 border-green-500/30 gap-1.5">
        <CheckCircle className="w-3 h-3" />
        Ready
      </Badge>
    );
  }
  if (status === "processing") {
    return (
      <Badge className="bg-yellow-500/10 text-yellow-600 border-yellow-500/30 gap-1.5 animate-pulse">
        <Loader2 className="w-3 h-3 animate-spin" />
        Indexing
      </Badge>
    );
  }
  return (
    <Badge className="bg-red-500/10 text-red-600 border-red-500/30 gap-1.5">
      <AlertCircle className="w-3 h-3" />
      Failed
    </Badge>
  );
}

interface BookMetaPanelProps {
  book: Book;
  shelfName?: string;
}

export default function BookMetaPanel({ book, shelfName }: BookMetaPanelProps) {
  const router = useRouter();
  const updateBook = useUpdateBook(book.library_id);
  const deleteBook = useDeleteBook(book.library_id);
  const moveBook = useMoveBook(book.library_id);
  const { data: shelvesData } = useShelves(book.library_id);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(book.title);
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [selectedShelf, setSelectedShelf] = useState<string | "unshelved">(book.shelf_id || "unshelved");
  const menuRef = useRef<HTMLDivElement>(null);

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
    if (editTitle.trim() && editTitle.trim() !== book.title) {
      try {
        await updateBook.mutateAsync({ bookId: book.id, body: { title: editTitle.trim() } });
        toast.success("Book renamed.");
      } catch {
        toast.error("Failed to rename book.");
        setEditTitle(book.title);
      }
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditTitle(book.title);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    try {
      await deleteBook.mutateAsync(book.id);
      toast.success("Book deleted.");
      setShowDeleteDialog(false);
      router.push(`/library/${book.library_id}`);
    } catch {
      toast.error("Failed to delete book.");
    }
  };

  const handleMove = async () => {
    try {
      const shelfId = selectedShelf === "unshelved" ? null : selectedShelf;
      await moveBook.mutateAsync({ bookId: book.id, body: { shelf_id: shelfId } });
      setShowMoveDialog(false);
      toast.success("Book moved successfully.");
    } catch {
      toast.error("Failed to move book.");
    }
  };

  return (
    <div className="h-full bg-parchment border-r border-border/60 flex flex-col overflow-y-auto">
      {/* Book cover hero */}
      <div className="relative bg-gradient-to-b from-mahogany to-mahogany/80 p-6 text-white">
        {/* Decorative top stripe */}
        <div className="h-1 w-full bg-brass/60 rounded mb-4" />

        <div className="flex items-start gap-1 mb-1">
          <StatusBadge status={book.status} />
        </div>

        {isEditing ? (
          <div className="mt-3">
            <div className="flex items-center gap-1">
              <input
                autoFocus
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSave();
                  if (e.key === "Escape") handleCancel();
                }}
                className="w-full bg-black/20 text-white font-bold text-xl leading-tight px-2 py-1 rounded border border-white/20 focus:outline-none focus:border-brass/50"
              />
              <button onClick={handleSave} className="p-1.5 hover:bg-white/10 rounded text-emerald-400">
                <Check className="w-4 h-4" />
              </button>
              <button onClick={handleCancel} className="p-1.5 hover:bg-white/10 rounded text-rose-400">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col mt-3 group/booktitle relative" ref={menuRef}>
            <div className="flex items-start justify-between gap-2">
              <h2 className="text-xl font-bold leading-tight pr-6">{book.title}</h2>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  setShowMenu(!showMenu);
                }}
                className={`relative z-10 flex-shrink-0 p-1 rounded transition-opacity hover:bg-white/10 ${
                  showMenu ? "text-white bg-white/10" : "text-white/60 hover:text-white"
                }`}
              >
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>

            {showMenu && (
              <div className="absolute right-0 top-8 w-36 bg-ink border border-white/10 rounded-md shadow-xl overflow-hidden z-20 flex flex-col">
                <button
                  onClick={() => {
                    setShowMenu(false);
                    setEditTitle(book.title);
                    setIsEditing(true);
                  }}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-white hover:bg-white/10 transition-colors w-full text-left"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  Rename
                </button>
                <button
                  onClick={() => {
                    setShowMenu(false);
                    setShowMoveDialog(true);
                  }}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-white hover:bg-white/10 transition-colors w-full text-left"
                >
                  <HardDrive className="w-3.5 h-3.5" />
                  Move to Shelf
                </button>
                <button
                  onClick={() => {
                    setShowMenu(false);
                    setShowDeleteDialog(true);
                  }}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/20 transition-colors w-full text-left border-t border-white/10"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete
                </button>
              </div>
            )}
          </div>
        )}

        <p className="text-white/60 text-sm mt-1">{book.filename}</p>
      </div>

      {/* Metadata list */}
      <div className="flex-1 p-5 space-y-4">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">
          Document Details
        </h3>

        <MetaRow
          icon={<HardDrive className="w-4 h-4" />}
          label="File Size"
          value={formatFileSize(book.file_size)}
        />

        <MetaRow
          icon={<Hash className="w-4 h-4" />}
          label="Indexed Chunks"
          value={book.total_chunks > 0 ? book.total_chunks.toString() : "—"}
        />

        {shelfName && (
          <MetaRow
            icon={<Layers className="w-4 h-4" />}
            label="Shelf"
            value={shelfName}
          />
        )}

        <MetaRow
          icon={<BookOpen className="w-4 h-4" />}
          label="Format"
          value="PDF"
        />

        <MetaRow
          icon={<Clock className="w-4 h-4" />}
          label="Uploaded"
          value={formatDate(book.created_at)}
        />

        <MetaRow
          icon={<Clock className="w-4 h-4" />}
          label="Last Updated"
          value={formatDate(book.updated_at)}
        />

        {/* Processing message */}
        {book.status === "processing" && (
          <div className="mt-4 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
            <p className="text-xs text-yellow-700 dark:text-yellow-400 leading-relaxed">
              This book is still being indexed. The chat will be available once indexing is complete.
            </p>
          </div>
        )}

        {book.status === "failed" && (
          <div className="mt-4 p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
            <p className="text-xs text-red-700 dark:text-red-400 leading-relaxed">
              Ingestion failed for this book. Please try re-uploading the PDF.
            </p>
          </div>
        )}
      </div>

      <Dialog open={showMoveDialog} onOpenChange={setShowMoveDialog}>
        <DialogContent className="sm:max-w-md bg-ink text-white border-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <Layers className="w-5 h-5 text-brass" />
              Move Book
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            <label className="text-sm font-medium text-white/80">Select Destination Shelf</label>
            <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar pr-2">
              <button
                onClick={() => setSelectedShelf("unshelved")}
                className={`w-full text-left px-3 py-2 rounded-md border text-sm transition-colors ${
                  selectedShelf === "unshelved" 
                    ? "bg-brass/20 border-brass text-brass" 
                    : "border-white/10 hover:bg-white/5 text-white/70"
                }`}
              >
                (Unshelved - Library Root)
              </button>
              {shelvesData?.shelves.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedShelf(s.id)}
                  className={`w-full text-left px-3 py-2 rounded-md border text-sm transition-colors ${
                    selectedShelf === s.id 
                      ? "bg-brass/20 border-brass text-brass" 
                      : "border-white/10 hover:bg-white/5 text-white/70"
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMoveDialog(false)} className="border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white">
              Cancel
            </Button>
            <Button onClick={handleMove} disabled={moveBook.isPending} className="bg-brass text-ink hover:bg-brass-light">
              {moveBook.isPending ? "Moving..." : "Move Book"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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

function MetaRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="text-brass/70 mt-0.5 flex-shrink-0">{icon}</div>
      <div>
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-sm font-medium text-foreground mt-0.5">{value}</div>
      </div>
    </div>
  );
}
