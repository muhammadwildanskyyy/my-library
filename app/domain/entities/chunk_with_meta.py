"""
ChunkWithMeta — a retrieved chunk enriched with source book metadata.

Used by the RAG pipeline to build citations/references in generated answers.
No database migration needed — this is assembled via JOIN at query time.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class ChunkWithMeta:
    """
    A text chunk paired with its source book metadata.

    Built from a JOIN between chunks and books tables during
    similarity search, enabling the RAG pipeline to produce
    inline citations like [1], [2] in generated answers.
    """

    chunk_id: UUID
    book_id: UUID
    book_title: str
    filename: str
    chunk_index: int
    source_type: str  # "text" | "table"
    content: str
