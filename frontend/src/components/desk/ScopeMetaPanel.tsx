import { useState, useRef, useEffect } from "react";
import { Library, Layers, Clock, BookOpen, MessageSquare, Plus, MoreVertical, Edit2, Trash2 } from "lucide-react";
import type { Library as ApiLibrary, Shelf } from "@/types/api";
import { useChatSessions, useUpdateChatSession, useDeleteChatSession } from "@/hooks/useChatSession";
import { toast } from "sonner";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatSessionDate(iso: string): string {
  const d = new Date(iso);
  const months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"];
  return `Chat - ${d.getDate()} ${months[d.getMonth()]}, ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

interface ScopeMetaPanelProps {
  library?: ApiLibrary;
  shelf?: Shelf;
  books?: import("@/types/api").Book[];
  totalBooks?: number;
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  onBookClick?: (book: import("@/types/api").Book) => void;
}

export default function ScopeMetaPanel({ library, shelf, books = [], totalBooks, sessionId, setSessionId, onBookClick }: ScopeMetaPanelProps) {
  const isShelf = !!shelf;
  const title = shelf ? shelf.name : library?.name || "Loading...";
  const description = shelf ? shelf.description : library?.description;

  const { data: sessionsData } = useChatSessions(
    library?.id ?? null,
    isShelf ? shelf.id : null
  );

  // Sessions are already filtered by the backend based on shelf_id.
  const sessions = sessionsData?.sessions || [];

  const updateSession = useUpdateChatSession();
  const deleteSession = useDeleteChatSession();

  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const startEditing = (id: string, currentName: string) => {
    setOpenMenuId(null);
    setEditingSessionId(id);
    setEditValue(currentName);
  };

  const saveEdit = async () => {
    if (!editingSessionId) return;
    const id = editingSessionId;
    const newName = editValue.trim();

    const session = sessions.find((s) => s.id === id);
    const oldName = session ? (session.name || formatSessionDate(session.created_at)) : "";

    setEditingSessionId(null);
    setEditValue("");

    if (newName !== "" && newName !== oldName) {
      try {
        await updateSession.mutateAsync({ sessionId: id, body: { name: newName } });
        toast.success("Chat name updated successfully.");
      } catch (e) {
        toast.error("Failed to update chat name.");
      }
    }
  };

  const handleDelete = async (id: string) => {
    setOpenMenuId(null);
    if (window.confirm("Are you sure you want to delete this chat?")) {
      try {
        await deleteSession.mutateAsync(id);
        if (sessionId === id) setSessionId(null); // Reset session if active is deleted
        toast.success("Chat deleted successfully.");
      } catch (e) {
        toast.error("Failed to delete chat.");
      }
    }
  };

  return (
    <div className="h-full bg-parchment border-r border-border/60 flex flex-col overflow-y-auto">
      {/* Scope hero */}
      <div className="relative bg-gradient-to-b from-mahogany to-mahogany/80 p-6 text-white flex-shrink-0">
        {/* Decorative top stripe */}
        <div className="h-1 w-full bg-brass/60 rounded mb-4" />

        <div className="flex items-start gap-1 mb-1">
          <div className="flex items-center gap-1.5 text-xs font-medium bg-black/20 px-2 py-1 rounded-md">
            {isShelf ? <Layers className="w-3 h-3" /> : <Library className="w-3 h-3" />}
            {isShelf ? "Shelf Desk" : "Library Desk"}
          </div>
        </div>

        <h2 className="text-xl font-bold mt-3 leading-tight">{title}</h2>
        {description && <p className="text-white/80 text-sm mt-2">{description}</p>}
      </div>

      {/* Metadata list */}
      <div className="p-5 space-y-4 flex-shrink-0 border-b border-border/40">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">
          {isShelf ? "Shelf Details" : "Library Details"}
        </h3>

        {totalBooks !== undefined && (
          <MetaRow
            icon={<BookOpen className="w-4 h-4" />}
            label="Total Books"
            value={totalBooks.toString()}
          />
        )}

        {isShelf && library && (
          <MetaRow
            icon={<Library className="w-4 h-4" />}
            label="From Library"
            value={library.name}
          />
        )}

        {(shelf?.created_at || library?.created_at) && (
          <MetaRow
            icon={<Clock className="w-4 h-4" />}
            label="Created At"
            value={formatDate(shelf ? shelf.created_at : library!.created_at)}
          />
        )}

        {(shelf?.updated_at || library?.updated_at) && (
          <MetaRow
            icon={<Clock className="w-4 h-4" />}
            label="Last Updated"
            value={formatDate(shelf ? shelf.updated_at : library!.updated_at)}
          />
        )}
      </div>

      {/* Books List */}
      {books && books.length > 0 && (
        <div className="p-5 flex-shrink-0 border-b border-border/40">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">
            Books
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
            {books.map((book) => (
              <button
                key={book.id}
                onClick={() => onBookClick?.(book)}
                className="w-full text-left flex items-start gap-2 group"
                title={book.title}
              >
                <BookOpen className="w-3.5 h-3.5 text-brass/60 mt-0.5 flex-shrink-0 group-hover:text-brass transition-colors" />
                <span className="text-xs text-foreground/80 line-clamp-2 group-hover:text-foreground transition-colors">
                  {book.title}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Session History */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
            Chat History
          </h3>
          <button
            onClick={() => setSessionId(null)}
            className="flex items-center gap-1 px-2 py-1 bg-brass/10 hover:bg-brass/20 text-brass rounded-md text-[10px] font-medium transition-colors"
          >
            <Plus className="w-3 h-3" /> New
          </button>
        </div>

        <div className="space-y-1">
          {sessions.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-2">No chats found.</p>
          ) : (
            sessions.map((session) => (
              <div key={session.id} className="relative group flex items-center">
                {editingSessionId === session.id ? (
                  <div className="flex-1 flex items-center px-2 py-1.5 bg-background border border-border rounded-md mx-1 shadow-sm">
                    <input
                      autoFocus
                      type="text"
                      className="w-full bg-transparent text-xs text-foreground outline-none"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveEdit();
                        if (e.key === "Escape") setEditingSessionId(null);
                      }}
                      onBlur={saveEdit}
                    />
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => setSessionId(session.id)}
                      className={`flex-1 text-left px-3 py-2.5 rounded-md text-xs transition-colors flex items-center gap-2.5 pr-8 ${sessionId === session.id
                          ? "bg-brass/15 text-brass font-medium shadow-sm"
                          : "text-muted-foreground hover:bg-black/5 hover:text-foreground"
                        }`}
                    >
                      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                      <span className="truncate" title={session.name || formatSessionDate(session.created_at)}>
                        {session.name || formatSessionDate(session.created_at)}
                      </span>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenMenuId(openMenuId === session.id ? null : session.id);
                      }}
                      className={`absolute right-2 p-1 rounded transition-opacity ${openMenuId === session.id
                          ? "opacity-100 text-foreground"
                          : "opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground"
                        }`}
                    >
                      <MoreVertical className="w-3.5 h-3.5" />
                    </button>

                    {openMenuId === session.id && (
                      <div ref={menuRef} className="absolute right-0 top-8 z-50 w-32 bg-background text-foreground rounded-md shadow-md border border-border py-1 text-xs">
                        <button
                          onClick={() => startEditing(session.id, session.name || formatSessionDate(session.created_at))}
                          className="w-full text-left px-3 py-1.5 hover:bg-muted flex items-center gap-2"
                        >
                          <Edit2 className="w-3 h-3" /> Rename
                        </button>
                        <button
                          onClick={() => handleDelete(session.id)}
                          className="w-full text-left px-3 py-1.5 hover:bg-red-500/10 text-red-500 flex items-center gap-2"
                        >
                          <Trash2 className="w-3 h-3" /> Delete
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>
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
