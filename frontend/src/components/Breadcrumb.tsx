"use client";

import { ChevronLeft, BookOpen, Library, Layers, Bot } from "lucide-react";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useLibrary } from "@/hooks/useLibraries";
import { useBook } from "@/hooks/useBooks";

export default function Breadcrumb() {
  const params = useParams();
  const router = useRouter();

  const pathname = usePathname();

  const libraryId = params.libraryId as string | undefined;
  const bookId = params.bookId as string | undefined;
  const shelfId = params.shelfId as string | undefined;
  
  const isDeskPage = pathname?.includes("/desk");
  const isShelfPage = pathname?.includes("/shelf/");

  const { data: library } = useLibrary(libraryId || null);
  const { data: book } = useBook(bookId || null);

  const viewMode = bookId || isDeskPage ? "DESK" : isShelfPage ? "SHELF" : libraryId ? "STACKS" : "LOBBY";

  const goBack = () => {
    router.back();
  };

  const returnToLobby = () => {
    router.push("/library");
  };

  if (viewMode === "LOBBY") {
    return (
      <header className="h-14 px-6 flex items-center gap-3 border-b border-border/60 bg-parchment/80 backdrop-blur-sm sticky top-0 z-40">
        <Library className="w-5 h-5 text-brass" />
        <span className="font-semibold text-ink text-sm tracking-wide">
          AI Librarian
        </span>
      </header>
    );
  }

  return (
    <header className="h-14 px-6 flex items-center gap-2 border-b border-border/60 bg-parchment/80 backdrop-blur-sm sticky top-0 z-40">
      <button
        onClick={goBack}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors group mr-1"
      >
        <ChevronLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
        Back
      </button>

      <div className="flex items-center gap-2 text-sm">
        <button
          onClick={returnToLobby}
          className="text-muted-foreground hover:text-brass transition-colors flex items-center gap-1.5"
        >
          <Library className="w-4 h-4" />
          <span className="hidden sm:inline">Lobby</span>
        </button>

        {libraryId && (
          <>
            <span className="text-border">/</span>
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Layers className="w-4 h-4" />
              <button
                onClick={() => router.push(`/library/${libraryId}`)}
                className="font-medium text-foreground truncate max-w-[160px] hover:text-brass transition-colors"
              >
                {library?.name ?? "Library"}
              </button>
            </span>
          </>
        )}

        {viewMode === "SHELF" && (
          <>
            <span className="text-border">/</span>
            <span className="flex items-center gap-1.5 text-brass font-medium">
              <Layers className="w-4 h-4" />
              <span className="truncate max-w-[160px]">
                Shelf
              </span>
            </span>
          </>
        )}

        {viewMode === "DESK" && (
          <>
            <span className="text-border">/</span>
            <span className="flex items-center gap-1.5 text-brass font-medium">
              {bookId ? (
                <>
                  <BookOpen className="w-4 h-4" />
                  <span className="truncate max-w-[160px]">
                    {book?.title ?? "Book"}
                  </span>
                </>
              ) : (
                <>
                  <Bot className="w-4 h-4" />
                  <span className="truncate max-w-[160px]">
                    Librarian Desk
                  </span>
                </>
              )}
            </span>
          </>
        )}
      </div>
    </header>
  );
}
