import type { Book } from "@/types/api";
import BookSpine from "./BookSpine";

interface ShelfPlankProps {
  books: Book[];
  emptyMessage?: string;
  isDragOver?: boolean;
  onDragOver?: (e: React.DragEvent) => void;
  onDragLeave?: (e: React.DragEvent) => void;
  onDrop?: (e: React.DragEvent) => void;
  onBookClick: (book: Book) => void;
}

export default function ShelfPlank({
  books,
  emptyMessage = "Empty shelf plank",
  isDragOver = false,
  onDragOver,
  onDragLeave,
  onDrop,
  onBookClick,
}: ShelfPlankProps) {
  return (
    <div
      className={`relative transition-all duration-200 bg-[#2a180c] rounded-xl shadow-xl ${
        isDragOver ? "ring-2 ring-brass scale-[1.01]" : ""
      }`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {/* Back panel */}
      <div
        className="absolute inset-0 shelf-wood opacity-30 rounded-xl"
        style={{ background: "oklch(0.3 0.05 40)" }}
      />

      {/* Books container */}
      <div className="relative z-10 px-5 pt-4 pb-0 flex items-end gap-[3px] min-h-[180px] flex-wrap justify-start">
        {books.length === 0 && (
          <div className="w-full flex items-center justify-center pb-8 text-white/20 text-sm italic">
            {emptyMessage}
          </div>
        )}
        {books.map((book) => (
          <BookSpine key={book.id} book={book} onClick={() => onBookClick(book)} />
        ))}
      </div>

      {/* Shelf Plank */}
      <div className="relative z-20 shelf-wood h-6 w-full rounded-b-xl border-t border-[#8a5a3a] border-b-2 border-black/60 shadow-[0_4px_12px_rgba(0,0,0,0.8)]" />
    </div>
  );
}
