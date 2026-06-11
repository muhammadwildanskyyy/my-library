"""
LangChain-based text chunker using ``langchain_text_splitters``.

Replaces the manual ``TiktokenChunker`` with LangChain's
``RecursiveCharacterTextSplitter`` or ``TokenTextSplitter``, producing
``Document`` objects directly compatible with the LangChain retriever
ecosystem (PGVector, EnsembleRetriever, etc.).

Table segments are kept as single documents (not split further) since
tables are typically short and should remain atomic for accurate retrieval.
"""

from __future__ import annotations

import logging
from typing import Any

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class LangChainChunker:
    """
    Chunk extracted PDF segments into ``Document`` objects.

    Supports two strategies:
    - ``recursive`` (default): ``RecursiveCharacterTextSplitter`` — splits by
      paragraph → sentence → word boundaries, preserving semantic coherence.
    - ``token``: ``TokenTextSplitter`` — splits by exact token count using
      ``tiktoken`` (cl100k_base encoding).

    Output ``Document`` objects carry rich metadata for downstream filtering
    and citation generation.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()

        self._strategy = s.CHUNK_STRATEGY
        self._splitter = self._create_splitter(s)
        self._encoding = tiktoken.get_encoding("cl100k_base")

    @staticmethod
    def _create_splitter(
        s: Settings,
    ) -> RecursiveCharacterTextSplitter | TokenTextSplitter:
        if s.CHUNK_STRATEGY == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=s.CHUNK_SIZE,
                chunk_overlap=s.CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", ". ", ", ", " ", ""],
                is_separator_regex=False,
            )
        else:  # "token"
            return TokenTextSplitter(
                encoding_name="cl100k_base",
                chunk_size=s.CHUNK_SIZE,
                chunk_overlap=s.CHUNK_OVERLAP,
            )

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken cl100k_base encoding."""
        return len(self._encoding.encode(text))

    def split_segments(
        self,
        segments: list[dict[str, Any]],
        metadata: dict[str, str],
    ) -> list[Document]:
        """
        Split extracted PDF segments into LangChain ``Document`` objects.

        Args:
            segments: List of extracted segments from ``pdf_extractor``.
                Each has ``content``, ``type`` (``"text"``/``"table"``), and ``page``.
            metadata: Base metadata dict applied to every chunk.
                Must include ``user_id``, ``library_id``, ``book_id``, etc.

        Returns:
            List of ``Document`` objects with enriched metadata including
            ``chunk_index``, ``source_type``, ``token_count``, and ``page``.
        """
        all_docs: list[Document] = []

        for segment in segments:
            source_type = segment.get("type", "text")
            page = segment.get("page", 0)

            segment_meta = {
                **metadata,
                "source_type": source_type,
                "page": str(page),
            }

            if source_type == "table":
                # Tables are kept as single atomic documents
                doc = Document(
                    page_content=segment["content"],
                    metadata={
                        **segment_meta,
                        "token_count": str(self._count_tokens(segment["content"])),
                    },
                )
                all_docs.append(doc)
            else:
                # Text is split using the configured strategy
                text_docs = self._splitter.create_documents(
                    texts=[segment["content"]],
                    metadatas=[segment_meta],
                )
                # Add token counts
                for doc in text_docs:
                    doc.metadata["token_count"] = str(
                        self._count_tokens(doc.page_content)
                    )
                all_docs.extend(text_docs)

        # Assign sequential chunk_index across all documents
        for idx, doc in enumerate(all_docs):
            doc.metadata["chunk_index"] = str(idx)

        logger.info(
            "Chunked %d segments into %d documents (strategy=%s)",
            len(segments),
            len(all_docs),
            self._strategy,
        )
        return all_docs
