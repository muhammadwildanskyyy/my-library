"use client";

import { useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useBook, useBooksByLibrary } from "@/hooks/useBooks";
import { useShelf } from "@/hooks/useShelves";
import { useLibrary } from "@/hooks/useLibraries";
import type { ReferenceItem } from "@/types/api";
import BookMetaPanel from "./BookMetaPanel";
import ScopeMetaPanel from "./ScopeMetaPanel";
import ChatPanel from "./ChatPanel";
import BookReaderPanel from "./BookReaderPanel";
import DragDeleteZone from "../library/DragDeleteZone";
import MainBookViewer from "./MainBookViewer";

/** Tracks which book + chunk the user navigated to from a reference click */
interface ActiveRef {
  bookId: string;
  bookTitle: string;
  chunkIndex?: number;
}

export default function DeskView({ libraryId, bookId }: { libraryId: string; bookId?: string }) {
  const searchParams = useSearchParams();
  const shelfId = searchParams.get("shelfId") || null;

  // Lifted Chat Session State
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Reference tracking — null means show default left panel
  const [activeRef, setActiveRef] = useState<ActiveRef | null>(null);

  const [leftPanelWidth, setLeftPanelWidth] = useState(320);
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    const startX = e.clientX;
    const startWidth = leftPanelWidth;

    const handleMouseMove = (mouseMoveEvent: MouseEvent) => {
      const newWidth = Math.max(250, Math.min(800, startWidth + (mouseMoveEvent.clientX - startX)));
      setLeftPanelWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }, [leftPanelWidth]);

  const { data: library, isLoading: libraryLoading } = useLibrary(libraryId);
  const { data: shelf, isLoading: shelfLoading } = useShelf(libraryId, shelfId);
  
  // Only fetch book if bookId is provided
  const { data: book, isLoading: bookLoading } = useBook(bookId || null);

  // Fetch the referenced book (may differ from the current desk book)
  const { data: referencedBook } = useBook(activeRef?.bookId ?? null);
  
  // Fetch all books in the library to count them
  const { data: booksData } = useBooksByLibrary(libraryId);
  
  const isLoading = (bookId && bookLoading) || libraryLoading || (shelfId && shelfLoading);

  /** Called when user clicks a reference chip or [N] marker in chat */
  const handleRefClick = useCallback((ref: ReferenceItem) => {
    setActiveRef({
      bookId: ref.book_id,
      bookTitle: ref.book_title,
      chunkIndex: ref.chunk_index,
    });
  }, []);

  /** Called when user clicks "Kembali" in the BookReaderPanel */
  const handleReaderClose = useCallback(() => {
    setActiveRef(null);
  }, []);

  if (isLoading || (bookId && !book)) {
    return (
      <div className="h-[calc(100vh-3.5rem)] flex">
        {/* Left skeleton */}
        <div className="w-80 border-r border-border bg-parchment animate-pulse" />
        {/* Right skeleton */}
        <div className="flex-1 bg-background animate-pulse" />
      </div>
    );
  }

  // Calculate total books in the current scope
  let totalBooks = 0;
  let scopeBooks: typeof booksData.books = [];
  if (booksData) {
    if (shelfId) {
      scopeBooks = booksData.books.filter((b) => b.shelf_id === shelfId);
    } else {
      scopeBooks = booksData.books;
    }
    totalBooks = scopeBooks.length;
  }

  // Decide what to show in the left panel
  const showBookReader = activeRef !== null && referencedBook !== undefined;

  return (
    <div className="h-[calc(100vh-3.5rem)] flex overflow-hidden">
      {/* Left panel — swaps between metadata and book reader */}
      <div 
        className="flex-shrink-0 overflow-hidden"
        style={{ width: `${leftPanelWidth}px` }}
      >
        {showBookReader ? (
          <BookReaderPanel
            book={referencedBook}
            highlightChunkIndex={activeRef.chunkIndex}
            isDragging={isDragging}
            onClose={handleReaderClose}
          />
        ) : bookId && book ? (
          <BookMetaPanel book={book} shelfName={shelf?.name} />
        ) : (
          <ScopeMetaPanel 
            library={library} 
            shelf={shelf} 
            books={scopeBooks}
            totalBooks={totalBooks} 
            sessionId={sessionId}
            setSessionId={setSessionId}
            onBookClick={(b) => setActiveRef({ bookId: b.id, bookTitle: b.title })}
          />
        )}
      </div>

      {/* Resizer Handle */}
      <div 
        className="w-1 cursor-col-resize hover:bg-brass/50 active:bg-brass/80 bg-border/40 transition-colors z-10 flex-shrink-0"
        onMouseDown={handleMouseDown}
      />

      {/* Right panel — AI Chat or PDF Viewer */}
      <div className="flex-1 min-w-0 overflow-hidden bg-background">
        {bookId && book ? (
          <MainBookViewer book={book} isDragging={isDragging} />
        ) : (
          <ChatPanel 
            libraryId={libraryId} 
            sessionId={sessionId}
            setSessionId={setSessionId}
            onRefClick={handleRefClick}
          />
        )}
      </div>

      {/* Global Drag to Delete Zone */}
      <DragDeleteZone libraryId={libraryId} />
    </div>
  );
}
