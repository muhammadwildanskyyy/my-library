"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Upload, X, Bot, Edit2 } from "lucide-react";
import { useShelves, useCreateShelf } from "@/hooks/useShelves";
import { useBooksByLibrary } from "@/hooks/useBooks";
import { useUploadBook } from "@/hooks/useUploadBook";
import { useLibrary, useUpdateLibrary } from "@/hooks/useLibraries";
import ShelfRow from "./ShelfRow";
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
import type { Book, Shelf } from "@/types/api";

export default function StacksView({ libraryId: activeLibraryId }: { libraryId: string }) {
  const router = useRouter();

  const { data: library } = useLibrary(activeLibraryId);
  const { data: shelvesData, isLoading: shelvesLoading } = useShelves(activeLibraryId);
  const { data: booksData, isLoading: booksLoading } = useBooksByLibrary(activeLibraryId);
  const createShelf = useCreateShelf(activeLibraryId ?? "");
  const updateLibrary = useUpdateLibrary();
  const uploadBook = useUploadBook();

  // Dialog states
  const [shelfDialogOpen, setShelfDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadTargetShelfId, setUploadTargetShelfId] = useState<string | null>(null);

  // Shelf form
  const [shelfName, setShelfName] = useState("");
  const [shelfDesc, setShelfDesc] = useState("");

  // Upload form
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");

  // Edit Library
  const [editLibraryOpen, setEditLibraryOpen] = useState(false);
  const [editLibraryName, setEditLibraryName] = useState("");
  const [editLibraryDesc, setEditLibraryDesc] = useState("");

  // Group books by shelf_id — computed once
  const grouped = useMemo(() => {
    const books = booksData?.books ?? [];
    const map = new Map<string | null, Book[]>();

    // Ensure all shelves are in the map (even empty ones)
    (shelvesData?.shelves ?? []).forEach((s) => map.set(s.id, []));
    map.set(null, []); // unshelved

    books.forEach((book) => {
      const key = book.shelf_id ?? null;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(book);
    });

    return map;
  }, [booksData, shelvesData]);

  const shelves: Shelf[] = shelvesData?.shelves ?? [];

  async function handleCreateShelf() {
    if (!shelfName.trim() || !activeLibraryId) return;
    try {
      await createShelf.mutateAsync({ name: shelfName.trim(), description: shelfDesc.trim() || undefined });
      setShelfDialogOpen(false);
      setShelfName("");
      setShelfDesc("");
      toast.success("Shelf created!");
    } catch {
      toast.error("Failed to create shelf.");
    }
  }

  function openUpload(shelfId: string | null) {
    setUploadTargetShelfId(shelfId);
    setUploadFile(null);
    setUploadTitle("");
    setUploadDialogOpen(true);
  }

  async function handleUpload() {
    if (!uploadFile || !uploadTitle.trim() || !activeLibraryId) return;
    try {
      await uploadBook.mutateAsync({
        libraryId: activeLibraryId,
        file: uploadFile,
        title: uploadTitle.trim(),
        shelfId: uploadTargetShelfId,
      });
      setUploadDialogOpen(false);
      toast.success("Book uploaded! Indexing in progress…");
    } catch {
      toast.error("Upload failed. Check file type (PDF only).");
    }
  }

  function openEditLibrary() {
    if (!library) return;
    setEditLibraryName(library.name);
    setEditLibraryDesc(library.description || "");
    setEditLibraryOpen(true);
  }

  async function handleEditLibrary() {
    if (!editLibraryName.trim() || !library) return;
    try {
      await updateLibrary.mutateAsync({
        libraryId: library.id,
        body: { name: editLibraryName.trim(), description: editLibraryDesc.trim() || null } as any
      });
      setEditLibraryOpen(false);
      toast.success("Library updated.");
    } catch {
      toast.error("Failed to update library.");
    }
  }

  const isLoading = shelvesLoading || booksLoading;

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-gradient-to-b from-aged-paper to-parchment">
      {/* Library title bar */}
      <div className="px-8 py-8">
        <div className="max-w-5xl mx-auto flex items-end justify-between gap-4">
          <div className="group relative">
            <div className="flex items-center gap-2">
              <h2 className="text-3xl font-bold text-ink tracking-tight">
                {library?.name ?? "Library"}
              </h2>
              <button 
                onClick={openEditLibrary} 
                className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-black/5 rounded transition-all"
                title="Edit Library"
              >
                <Edit2 className="w-4 h-4" />
              </button>
            </div>
            {library?.description ? (
              <p className="text-muted-foreground text-sm mt-1 max-w-2xl">
                {library.description}
              </p>
            ) : (
              <p 
                className="text-muted-foreground/50 text-sm mt-1 italic cursor-pointer hover:text-muted-foreground transition-colors w-max" 
                onClick={openEditLibrary}
              >
                + Add description
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => router.push(`/library/${activeLibraryId}/desk`)}
              className="border-brass/40 text-muted-foreground hover:border-brass hover:text-foreground bg-white/50 backdrop-blur-sm"
            >
              <Bot className="w-3.5 h-3.5 mr-1.5" />
              Ask Librarian
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShelfDialogOpen(true)}
              className="border-brass/40 text-muted-foreground hover:border-brass hover:text-foreground"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              New Shelf
            </Button>
            <Button
              size="sm"
              onClick={() => openUpload(null)}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              <Upload className="w-3.5 h-3.5 mr-1.5" />
              Upload Book
            </Button>
          </div>
        </div>
      </div>

      {/* Shelves */}
      <div className="px-8 pb-16 max-w-5xl mx-auto">
        {isLoading && (
          <div className="space-y-8">
            {[1, 2].map((i) => (
              <div key={i}>
                <div className="h-4 w-32 bg-muted rounded animate-pulse mb-3" />
                <div className="h-48 bg-muted rounded-xl animate-pulse" />
              </div>
            ))}
          </div>
        )}

        {!isLoading && (
          <>
            {/* Named shelves */}
            {shelves.map((shelf) => (
              <ShelfRow
                key={shelf.id}
                libraryId={activeLibraryId}
                shelf={shelf}
                books={grouped.get(shelf.id) ?? []}
                onAddBook={() => openUpload(shelf.id)}
              />
            ))}

            {/* Unshelved row — only show if there are unshelved books */}
            {(grouped.get(null)?.length ?? 0) > 0 && (
              <ShelfRow
                libraryId={activeLibraryId}
                shelf={null}
                books={grouped.get(null) ?? []}
                onAddBook={() => openUpload(null)}
              />
            )}

            {shelves.length === 0 && (grouped.get(null)?.length ?? 0) === 0 && (
              <div className="text-center py-20 text-muted-foreground">
                <p className="text-lg font-medium mb-2">This library is empty.</p>
                <p className="text-sm">Create a shelf or upload your first book to get started.</p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Create shelf dialog */}
      <Dialog open={shelfDialogOpen} onOpenChange={setShelfDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Shelf</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-2">
            <Input
              placeholder="Shelf name"
              value={shelfName}
              onChange={(e) => setShelfName(e.target.value)}
              autoFocus
            />
            <Textarea
              placeholder="Description (optional)"
              value={shelfDesc}
              onChange={(e) => setShelfDesc(e.target.value)}
              rows={2}
              className="resize-none"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShelfDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreateShelf}
              disabled={!shelfName.trim() || createShelf.isPending}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              {createShelf.isPending ? "Creating…" : "Create Shelf"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Library Dialog */}
      <Dialog open={editLibraryOpen} onOpenChange={setEditLibraryOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Library</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-2 mt-2">
            <div>
              <label className="text-sm font-medium text-foreground block mb-2">Library Name</label>
              <Input
                placeholder="E.g., Personal Collection"
                value={editLibraryName}
                onChange={(e) => setEditLibraryName(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground block mb-2">Description</label>
              <Textarea
                placeholder="Add a brief description (optional)"
                value={editLibraryDesc}
                onChange={(e) => setEditLibraryDesc(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditLibraryOpen(false)}>Cancel</Button>
            <Button
              onClick={handleEditLibrary}
              disabled={!editLibraryName.trim() || updateLibrary.isPending}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              {updateLibrary.isPending ? "Saving…" : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload book dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-4 h-4 text-brass" />
              Upload Book (PDF)
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-2">
            <Input
              placeholder="Book title"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              autoFocus
            />

            {/* File drop zone */}
            <label className="border-2 border-dashed border-border hover:border-brass/60 rounded-xl p-6 cursor-pointer flex flex-col items-center gap-2 transition-colors group">
              <input
                type="file"
                accept="application/pdf"
                className="sr-only"
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null;
                  setUploadFile(f);
                  if (f && !uploadTitle) setUploadTitle(f.name.replace(/\.pdf$/i, ""));
                }}
              />
              {uploadFile ? (
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-foreground truncate max-w-[240px]">
                    {uploadFile.name}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); setUploadFile(null); }}
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
            <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleUpload}
              disabled={!uploadFile || !uploadTitle.trim() || uploadBook.isPending}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              {uploadBook.isPending ? "Uploading…" : "Upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Global Drag to Delete Zone */}
      <DragDeleteZone libraryId={activeLibraryId} />
    </div>
  );
}
