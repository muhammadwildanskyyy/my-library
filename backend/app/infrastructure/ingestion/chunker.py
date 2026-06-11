"""
Token-aware text chunker using tiktoken.

Splits text into chunks of approximately CHUNK_SIZE tokens
with CHUNK_OVERLAP tokens of overlap between consecutive chunks.
"""

import logging

import tiktoken

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class TiktokenChunker:
    """
    Chunk text based on token count using tiktoken.

    Uses cl100k_base encoding (compatible with OpenAI and general-purpose).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self._chunk_size = s.CHUNK_SIZE
        self._chunk_overlap = s.CHUNK_OVERLAP
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self._encoding.encode(text))

    def chunk_text(self, text: str) -> list[dict]:
        """
        Split text into token-sized chunks with overlap.

        Returns:
            List of dicts: [{"content": "...", "token_count": 123}, ...]
        """
        if not text.strip():
            return []

        # Split by paragraphs first to preserve semantic boundaries
        paragraphs = text.split("\n\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: list[dict] = []
        current_chunk: list[str] = []
        current_tokens = 0

        for paragraph in paragraphs:
            para_tokens = self.count_tokens(paragraph)

            # If a single paragraph exceeds chunk size, split by sentences
            if para_tokens > self._chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(
                        {
                            "content": chunk_text,
                            "token_count": self.count_tokens(chunk_text),
                        }
                    )
                    current_chunk = []
                    current_tokens = 0

                # Split large paragraph by sentences
                sentence_chunks = self._split_large_text(paragraph)
                chunks.extend(sentence_chunks)
                continue

            # Check if adding this paragraph exceeds the limit
            if current_tokens + para_tokens > self._chunk_size and current_chunk:
                # Emit current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    {
                        "content": chunk_text,
                        "token_count": self.count_tokens(chunk_text),
                    }
                )

                # Keep overlap: retain the last paragraph(s) for context
                overlap_chunk: list[str] = []
                overlap_tokens = 0
                for p in reversed(current_chunk):
                    p_tokens = self.count_tokens(p)
                    if overlap_tokens + p_tokens <= self._chunk_overlap:
                        overlap_chunk.insert(0, p)
                        overlap_tokens += p_tokens
                    else:
                        break

                current_chunk = overlap_chunk
                current_tokens = overlap_tokens

            current_chunk.append(paragraph)
            current_tokens += para_tokens

        # Flush remaining
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(
                {
                    "content": chunk_text,
                    "token_count": self.count_tokens(chunk_text),
                }
            )

        logger.info(
            f"Chunked text into {len(chunks)} chunks "
            f"(target size: {self._chunk_size} tokens)"
        )
        return chunks

    def _split_large_text(self, text: str) -> list[dict]:
        """Split a text larger than chunk_size by sentences."""
        # Split by common sentence delimiters
        sentences = []
        for part in text.replace(". ", ".\n").split("\n"):
            part = part.strip()
            if part:
                sentences.append(part)

        chunks: list[dict] = []
        current_parts: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            s_tokens = self.count_tokens(sentence)

            if current_tokens + s_tokens > self._chunk_size and current_parts:
                chunk_text = " ".join(current_parts)
                chunks.append(
                    {
                        "content": chunk_text,
                        "token_count": self.count_tokens(chunk_text),
                    }
                )
                current_parts = []
                current_tokens = 0

            current_parts.append(sentence)
            current_tokens += s_tokens

        if current_parts:
            chunk_text = " ".join(current_parts)
            chunks.append(
                {
                    "content": chunk_text,
                    "token_count": self.count_tokens(chunk_text),
                }
            )

        return chunks

    def chunk_segments(self, segments: list[dict]) -> list[dict]:
        """
        Chunk a list of extracted segments (text or table).

        Table segments are kept as single chunks (not split further).
        Text segments are chunked normally.

        Returns:
            List of dicts: [{"content": "...", "token_count": N, "source_type": "text"|"table"}, ...]
        """
        all_chunks: list[dict] = []

        for segment in segments:
            source_type = segment.get("type", "text")

            if source_type == "table":
                # Tables are kept as single chunks
                token_count = self.count_tokens(segment["content"])
                all_chunks.append(
                    {
                        "content": segment["content"],
                        "token_count": token_count,
                        "source_type": "table",
                    }
                )
            else:
                # Text is chunked
                text_chunks = self.chunk_text(segment["content"])
                for chunk in text_chunks:
                    chunk["source_type"] = "text"
                    all_chunks.append(chunk)

        return all_chunks
