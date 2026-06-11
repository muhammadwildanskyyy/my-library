"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, BookOpen, CalendarDays, BookMarked, Edit2, Check, X, MoreVertical } from "lucide-react";
import { useLibraries, useCreateLibrary, useDeleteLibrary, useUpdateLibrary } from "@/hooks/useLibraries";
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
import type { Library } from "@/types/api";

// Decorative "door" number colors for each library card
const CARD_ACCENTS = [
  { bg: "from-mahogany/90 to-mahogany", border: "border-brass/40" },
  { bg: "from-spine-navy to-spine-navy/90", border: "border-brass/30" },
  { bg: "from-spine-forest to-spine-forest/90", border: "border-brass/30" },
  { bg: "from-spine-plum to-spine-plum/90", border: "border-brass/30" },
  { bg: "from-spine-terracotta to-spine-terracotta/90", border: "border-brass/30" },
  { bg: "from-spine-slate to-spine-slate/90", border: "border-brass/30" },
];

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function LibraryDoorCard({
  library,
  index,
  onEnter,
  onDelete,
  onUpdate,
}: {
  library: Library;
  index: number;
  onEnter: (id: string) => void;
  onDelete: (id: string) => void;
  onUpdate: (id: string, newName: string) => void;
}) {
  const accent = CARD_ACCENTS[index % CARD_ACCENTS.length];
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(library.name);
  const [showMenu, setShowMenu] = useState(false);
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

  const handleSave = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    if (editName.trim() && editName.trim() !== library.name) {
      onUpdate(library.id, editName.trim());
    }
    setIsEditing(false);
  };

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditName(library.name);
    setIsEditing(false);
  };

  return (
    <div
      className={`relative group cursor-pointer rounded-2xl border-2 ${accent.border} bg-gradient-to-br ${accent.bg} overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1`}
      onClick={() => {
        if (!isEditing) onEnter(library.id);
      }}
    >
      {/* Brass plate ornament */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 w-16 h-4 bg-brass/80 rounded-sm shadow-sm" />

      {/* Door knocker knob */}
      <div className="absolute top-5 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-brass shadow-inner border border-brass-light/60" />

      {/* Door panels (decorative lines) */}
      <div className="absolute inset-4 border border-white/10 rounded-xl pointer-events-none" />
      <div className="absolute inset-7 border border-white/5 rounded-lg pointer-events-none" />

      {/* Content */}
      <div className="relative p-6 pt-12 flex flex-col gap-3 min-h-[220px]">
        <div className="flex items-start justify-between gap-2">
          {isEditing ? (
            <div className="flex-1 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <input
                autoFocus
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSave(e);
                  if (e.key === "Escape") handleCancel(e as any);
                }}
                className="w-full bg-black/20 text-white font-bold text-lg leading-tight px-2 py-1 rounded border border-white/20 focus:outline-none focus:border-brass/50"
              />
              <button
                onClick={handleSave}
                className="p-1.5 rounded-md hover:bg-white/10 text-emerald-400"
                title="Save"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={handleCancel}
                className="p-1.5 rounded-md hover:bg-white/10 text-rose-400"
                title="Cancel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              <h3 className="text-white font-bold text-lg leading-tight flex-1">
                {library.name}
              </h3>
              <div className="relative z-10" ref={menuRef}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    setShowMenu(!showMenu);
                  }}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-white/10 text-white/60 hover:text-white"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>

                {showMenu && (
                  <div className="absolute right-0 top-full mt-1 w-32 bg-ink/95 border border-white/10 rounded-md shadow-xl overflow-hidden z-10 flex flex-col">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowMenu(false);
                        setIsEditing(true);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-white hover:bg-white/10 transition-colors w-full text-left"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                      Rename
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowMenu(false);
                        onDelete(library.id);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/20 transition-colors w-full text-left border-t border-white/10"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {library.description && (
          <p className="text-white/70 text-sm line-clamp-2 leading-relaxed">
            {library.description}
          </p>
        )}

        <div className="mt-auto pt-4 border-t border-white/10 flex items-center justify-between text-white/50 text-xs">
          <span className="flex items-center gap-1">
            <CalendarDays className="w-3 h-3" />
            {formatDate(library.created_at)}
          </span>
          <span className="flex items-center gap-1">
            <BookOpen className="w-3 h-3" />
            Enter
          </span>
        </div>
      </div>

      {/* Hover glow */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity bg-white/5 pointer-events-none" />
    </div>
  );
}

export default function LobbyView() {
  const router = useRouter();
  const { data, isLoading, isError } = useLibraries();
  const createLibrary = useCreateLibrary();
  const deleteLibrary = useDeleteLibrary();
  const updateLibrary = useUpdateLibrary();

  const enterLibrary = (id: string) => {
    router.push(`/library/${id}`);
  };

  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleCreate() {
    if (!name.trim()) return;
    try {
      await createLibrary.mutateAsync({ name: name.trim(), description: description.trim() || undefined });
      setDialogOpen(false);
      setName("");
      setDescription("");
      toast.success("Library created!");
    } catch {
      toast.error("Failed to create library.");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteLibrary.mutateAsync(id);
      toast.success("Library deleted.");
    } catch {
      toast.error("Failed to delete library.");
    }
  }

  async function handleUpdate(id: string, newName: string) {
    try {
      await updateLibrary.mutateAsync({ libraryId: id, body: { name: newName } });
      toast.success("Library renamed.");
    } catch {
      toast.error("Failed to rename library.");
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-gradient-to-b from-parchment to-aged-paper">
      {/* Grand hall header */}
      <div className="text-center py-14 px-6">
        <div className="flex items-center justify-center gap-3 mb-4">
          <BookMarked className="w-8 h-8 text-brass" />
          <h1 className="text-4xl font-bold text-ink tracking-tight">
            Grand Library
          </h1>
        </div>
        <p className="text-muted-foreground text-base max-w-md mx-auto">
          Select a library to enter, or create a new collection of knowledge.
        </p>

        {/* Ornamental divider */}
        <div className="flex items-center justify-center gap-4 mt-6">
          <div className="h-px w-24 bg-brass/30" />
          <div className="w-2 h-2 rounded-full bg-brass/50" />
          <div className="h-px w-24 bg-brass/30" />
        </div>
      </div>

      {/* Library doors grid */}
      <div className="max-w-5xl mx-auto px-6 pb-16">
        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-56 rounded-2xl bg-muted animate-pulse"
              />
            ))}
          </div>
        )}

        {isError && (
          <div className="text-center text-destructive py-12">
            Failed to load libraries. Is the backend running?
          </div>
        )}

        {data && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.libraries.map((lib, i) => (
              <LibraryDoorCard
                key={lib.id}
                library={lib}
                index={i}
                onEnter={enterLibrary}
                onDelete={handleDelete}
                onUpdate={handleUpdate}
              />
            ))}

            {/* New library card */}
            <button
              onClick={() => setDialogOpen(true)}
              className="group relative rounded-2xl border-2 border-dashed border-brass/30 bg-parchment/50 hover:bg-parchment hover:border-brass/60 transition-all duration-300 min-h-[220px] flex flex-col items-center justify-center gap-3 shadow-sm hover:shadow-md hover:-translate-y-1"
            >
              <div className="w-12 h-12 rounded-full bg-brass/10 group-hover:bg-brass/20 flex items-center justify-center transition-colors">
                <Plus className="w-6 h-6 text-brass" />
              </div>
              <span className="text-muted-foreground group-hover:text-brass font-medium transition-colors text-sm">
                New Library
              </span>
            </button>
          </div>
        )}
      </div>

      {/* Create library dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BookMarked className="w-5 h-5 text-brass" />
              Create New Library
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-2">
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">
                Library Name
              </label>
              <Input
                placeholder="e.g. AI Research Papers"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">
                Description{" "}
                <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <Textarea
                placeholder="A collection of..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!name.trim() || createLibrary.isPending}
              className="bg-mahogany hover:bg-mahogany-light text-white"
            >
              {createLibrary.isPending ? "Creating..." : "Create Library"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
