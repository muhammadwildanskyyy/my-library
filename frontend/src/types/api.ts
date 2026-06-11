/**
 * TypeScript interfaces derived from backend Pydantic schemas.
 * Source: app/api/v1/schemas/
 */

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  user: UserResponse;
  token: TokenResponse;
}

// ---------------------------------------------------------------------------
// Library  — GET /api/v1/libraries/  |  POST /api/v1/libraries/
// ---------------------------------------------------------------------------
export interface LibraryCreate {
  name: string;
  description?: string | null;
}

export interface LibraryUpdate {
  name?: string;
  description?: string | null;
}

export interface Library {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface LibraryListResponse {
  libraries: Library[];
  total: number;
}

// ---------------------------------------------------------------------------
// Shelf  — GET /api/v1/libraries/{library_id}/shelves/
// ---------------------------------------------------------------------------
export interface ShelfCreate {
  name: string;
  description?: string | null;
}

export interface ShelfUpdate {
  name?: string;
  description?: string | null;
}

export interface Shelf {
  id: string;
  library_id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShelfListResponse {
  shelves: Shelf[];
  total: number;
}

// ---------------------------------------------------------------------------
// Book  — GET /api/v1/libraries/{library_id}/books/
//          GET /api/v1/shelves/{shelf_id}/books/
//          POST /api/v1/libraries/{library_id}/books/  (multipart/form-data)
//          PATCH /api/v1/books/{book_id}/move
//          DELETE /api/v1/books/{book_id}
// ---------------------------------------------------------------------------
export type BookStatus = "processing" | "ready" | "failed";

export interface Book {
  id: string;
  library_id: string;
  shelf_id: string | null;
  user_id: string;
  title: string;
  filename: string;
  file_url: string | null;
  file_size: number;
  total_chunks: number;
  status: BookStatus;
  created_at: string;
  updated_at: string;
}

export interface BookListResponse {
  books: Book[];
  total: number;
}

export interface BookMoveRequest {
  shelf_id: string | null;
}

export interface BookUpdate {
  title?: string;
}

// ---------------------------------------------------------------------------
// Chat Session  — POST /api/v1/chat/sessions/
//                 GET  /api/v1/chat/sessions/?library_id=...
// ---------------------------------------------------------------------------
export interface ChatSessionCreate {
  library_id: string;
  shelf_id?: string | null;
}

export interface ChatSessionUpdate {
  name: string;
}

export interface ChatSession {
  id: string;
  library_id: string;
  shelf_id: string | null;
  name: string | null;
  created_at: string;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
  total: number;
}

// ---------------------------------------------------------------------------
// Chat Messages  — POST /api/v1/chat/sessions/{session_id}/messages/
//                  GET  /api/v1/chat/sessions/{session_id}/messages/
// ---------------------------------------------------------------------------
export interface ChatRequest {
  question: string;
}

export interface ReferenceItem {
  ref_index: number;
  book_id: string;
  book_title: string;
  filename: string;
  chunk_index: number;
  source_type: string;
}

export interface ChatResponse {
  answer: string;
  used_web: boolean;
  session_id: string;
  message_id: string;
  num_docs_retrieved: number;
  num_docs_relevant: number;
  references: ReferenceItem[];
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  from_web: boolean;
  token_count: number;
  // Citation references; only present on assistant messages
  references: ReferenceItem[];
  created_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  total: number;
}

// ---------------------------------------------------------------------------
// Book Chunks  — GET /api/v1/books/{book_id}/chunks/
// ---------------------------------------------------------------------------
export interface ChunkItem {
  chunk_index: number;
  content: string;
  source_type: string;
  page: string;
  token_count: string;
}

export interface BookChunksResponse {
  chunks: ChunkItem[];
  total: number;
}
