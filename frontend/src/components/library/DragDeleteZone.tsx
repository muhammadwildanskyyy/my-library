"use client";

import { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import { useDeleteBook } from "@/hooks/useBooks";
import { toast } from "sonner";
import { DeleteBookDialog } from "./DeleteBookDialog";

export default function DragDeleteZone({ libraryId }: { libraryId: string }) {
  const [isDraggingBook, setIsDraggingBook] = useState(false);
  const [isDragOverTrash, setIsDragOverTrash] = useState(false);
  const [bookToDelete, setBookToDelete] = useState<{ id: string } | null>(null);
  const deleteBook = useDeleteBook(libraryId);

  useEffect(() => {
    const handleDragStart = (e: DragEvent) => {
      const target = e.target as HTMLElement;
      // Only show trash zone if it's a book being dragged
      if (target?.getAttribute?.("data-book-id")) {
        setIsDraggingBook(true);
      }
    };

    const handleDragEnd = () => {
      setIsDraggingBook(false);
      setIsDragOverTrash(false);
    };

    document.addEventListener("dragstart", handleDragStart);
    document.addEventListener("dragend", handleDragEnd);
    return () => {
      document.removeEventListener("dragstart", handleDragStart);
      document.removeEventListener("dragend", handleDragEnd);
    };
  }, []);

  if (!isDraggingBook && !bookToDelete) return null;

  return (
    <>
      {isDraggingBook && (
        <div
          className={`fixed bottom-8 left-1/2 -translate-x-1/2 w-64 h-32 rounded-2xl flex flex-col items-center justify-center border-2 border-dashed transition-all z-[100] shadow-2xl ${
            isDragOverTrash 
              ? "bg-rose-500/90 border-rose-200 text-white scale-105 shadow-rose-500/50" 
              : "bg-zinc-900/90 border-zinc-500/50 text-zinc-400 backdrop-blur-md"
          }`}
          onDragOver={(e) => {
            // Allow dropping
            if (e.dataTransfer.types.includes("application/vnd.book.id")) {
              e.preventDefault();
              e.dataTransfer.dropEffect = "move";
              setIsDragOverTrash(true);
            }
          }}
          onDragLeave={() => setIsDragOverTrash(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDraggingBook(false);
            setIsDragOverTrash(false);
            
            const bookId = e.dataTransfer.getData("application/vnd.book.id");
            if (bookId) {
              setBookToDelete({ id: bookId });
            }
          }}
        >
          <Trash2 className={`w-10 h-10 mb-3 transition-transform ${isDragOverTrash ? "scale-110" : ""}`} />
          <span className="text-base font-semibold">{isDragOverTrash ? "Release to Delete" : "Drop book here to delete"}</span>
        </div>
      )}

      <DeleteBookDialog
        open={!!bookToDelete}
        onOpenChange={(open) => {
          if (!open) setBookToDelete(null);
        }}
        onConfirm={async () => {
          if (!bookToDelete) return;
          try {
            await deleteBook.mutateAsync(bookToDelete.id);
            setBookToDelete(null);
            toast.success("Book deleted successfully.");
          } catch (err) {
            console.error("Failed to delete book", err);
            toast.error("Failed to delete book.");
          }
        }}
        isDeleting={deleteBook.isPending}
      />
    </>
  );
}
