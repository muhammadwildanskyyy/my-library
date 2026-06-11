"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Upload, X, Bot, ChevronLeft, Edit2 } from "lucide-react";
import { useShelf, useUpdateShelf } from "@/hooks/useShelves";
import { useBooksByShelf } from "@/hooks/useBooks";
import { useUploadBook } from "@/hooks/useUploadBook";
import BookSpine from "./BookSpine";
import ShelfPlank from "./ShelfPlank";
import DragDeleteZone from "./DragDeleteZone";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

// Books per shelf plank in the bookcase
const BOOKS_PER_PLANK = 12;

export default function ShelfView({
  libraryId,
  shelfId,
}: {
  libraryId: string;
  shelfId: string;
}) {
  const router = useRouter();

  const { data: shelf, isLoading: shelfLoading } = useShelf(libraryId, shelfId);
  const { data: booksData, isLoading: booksLoading } = useBooksByShelf(shelfId);
  const updateShelf = useUpdateShelf(libraryId);
  const uploadBook = useUploadBook();

  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");

  const [editShelfOpen, setEditShelfOpen] = useState(false);
  const [editShelfName, setEditShelfName] = useState("");
  const [editShelfDesc, setEditShelfDesc] = useState("");

  const books = booksData?.books ?? [];
  const isLoading = shelfLoading || booksLoading;

  // Chunk books into multiple shelf planks
  const shelfChunks = [];
  for (let i = 0; i < Math.max(books.length, 1); i += BOOKS_PER_PLANK) {
    shelfChunks.push(books.slice(i, i + BOOKS_PER_PLANK));
  }

  function openUpload() {
    setUploadFile(null);
    setUploadTitle("");
    setUploadDialogOpen(true);
  }

  async function handleUpload() {
    if (!uploadFile || !uploadTitle.trim()) return;
    try {
      await uploadBook.mutateAsync({
        libraryId,
        file: uploadFile,
        title: uploadTitle.trim(),
        shelfId,
      });
      setUploadDialogOpen(false);
      toast.success("Book uploaded to shelf! Indexing in progress…");
    } catch {
      toast.error("Upload failed. Check file type (PDF only).");
    }
  }

  function openEditShelf() {
    if (!shelf) return;
    setEditShelfName(shelf.name);
    setEditShelfDesc(shelf.description || "");
    setEditShelfOpen(true);
  }

  async function handleEditShelf() {
    if (!editShelfName.trim() || !shelf) return;
    try {
      await updateShelf.mutateAsync({
        shelfId: shelf.id,
        body: { name: editShelfName.trim(), description: editShelfDesc.trim() || null } as any
      });
      setEditShelfOpen(false);
      toast.success("Shelf updated.");
    } catch {
      toast.error("Failed to update shelf.");
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-3.5rem)] bg-gradient-to-b from-aged-paper to-parchment p-8">
        <div className="max-w-5xl mx-auto space-y-8 animate-pulse">
          <div className="h-10 w-64 bg-muted rounded" />
          <div className="h-64 bg-muted rounded-xl" />
        </div>
      </div>
    );
  }

  if (!shelf) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Shelf not found.
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-gradient-to-b from-aged-paper to-parchment">
      {/* Header */}
      <div className="px-8 py-8 border-b border-border/30 bg-background/50 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto flex items-end justify-between gap-4 flex-wrap">
          <div className="group relative">
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={() => router.push(`/library/${libraryId}`)}
                className="text-muted-foreground hover:text-foreground transition-colors flex items-center text-sm"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back to Library
              </button>
            </div>
            <div className="flex items-center gap-2">
              <h2 className="text-3xl font-bold text-ink tracking-tight flex items-center gap-3">
                {shelf.name}
                <span className="text-sm font-normal text-muted-foreground bg-muted px-2 py-1 rounded-md">
                  {books.length} {books.length === 1 ? "book" : "books"}
                </span>
              </h2>
              <button 
                onClick={openEditShelf} 
                className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-black/5 rounded transition-all"
                title="Edit Shelf"
              >
                <Edit2 className="w-4 h-4" />
              </button>
            </div>
            {shelf.description ? (
              <p className="text-muted-foreground text-sm mt-2 max-w-2xl">
                {shelf.description}
              </p>
            ) : (
              <p 
                className="text-muted-foreground/50 text-sm mt-2 italic cursor-pointer hover:text-muted-foreground transition-colors w-max" 
                onClick={openEditShelf}
              >
                + Add description
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 mt-4 sm:mt-0">
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                router.push(`/library/${libraryId}/desk?shelfId=${shelfId}`)
              }
              className="border-brass/40 text-muted-foreground hover:border-brass hover:text-foreground bg-white/50 backdrop-blur-sm"
            >
              <Bot className="w-3.5 h-3.5 mr-1.5" />
              Ask Librarian
            </Button>
            <Button
              size="sm"
              onClick={openUpload}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Add Book
            </Button>
          </div>
        </div>
      </div>

      {/* Bookcase Planks */}
      <div className="px-8 py-12 max-w-5xl mx-auto flex flex-col gap-y-10">
        {shelfChunks.map((chunk, index) => (
          <ShelfPlank
            key={index}
            books={chunk}
            emptyMessage="Empty shelf plank"
            onBookClick={(book) =>
              router.push(
                `/library/${libraryId}/book/${book.id}?shelfId=${shelfId}`
              )
            }
          />
        ))}
      </div>

      {/* Upload dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-4 h-4 text-brass" />
              Upload Book to {shelf?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-2">
            <Input
              placeholder="Book title"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              autoFocus
            />

            <label className="border-2 border-dashed border-border hover:border-brass/60 rounded-xl p-6 cursor-pointer flex flex-col items-center gap-2 transition-colors group">
              <input
                type="file"
                accept="application/pdf"
                className="sr-only"
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null;
                  setUploadFile(f);
                  if (f && !uploadTitle)
                    setUploadTitle(f.name.replace(/\.pdf$/i, ""));
                }}
              />
              {uploadFile ? (
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-foreground truncate max-w-[240px]">
                    {uploadFile.name}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      setUploadFile(null);
                    }}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="w-6 h-6 text-muted-foreground group-hover:text-brass transition-colors" />
                  <span className="text-sm text-muted-foreground">
                    Click to select PDF
                  </span>
                </>
              )}
            </label>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setUploadDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={
                !uploadFile || !uploadTitle.trim() || uploadBook.isPending
              }
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              {uploadBook.isPending ? "Uploading…" : "Upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Shelf Dialog */}
      <Dialog open={editShelfOpen} onOpenChange={setEditShelfOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Shelf</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-2 mt-2">
            <div>
              <label className="text-sm font-medium text-foreground block mb-2">Shelf Name</label>
              <Input
                placeholder="E.g., Science Fiction"
                value={editShelfName}
                onChange={(e) => setEditShelfName(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground block mb-2">Description</label>
              <Textarea
                placeholder="Add a brief description (optional)"
                value={editShelfDesc}
                onChange={(e) => setEditShelfDesc(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditShelfOpen(false)}>Cancel</Button>
            <Button
              onClick={handleEditShelf}
              disabled={!editShelfName.trim() || updateShelf.isPending}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              {updateShelf.isPending ? "Saving…" : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Global Drag to Delete Zone */}
      <DragDeleteZone libraryId={libraryId} />
    </div>
  );
}
