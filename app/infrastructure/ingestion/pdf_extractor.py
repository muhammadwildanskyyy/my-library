"""
PDF text and table extraction using PyMuPDF (text) + pdfplumber (tables).

Tables are converted to Markdown format immediately upon extraction
and injected with surrounding text context.
"""

import io
import logging

import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger(__name__)


def _table_to_markdown(table: list[list]) -> str:
    """
    Convert a pdfplumber table (list of rows) to Markdown format.

    Example output:
        | Col1 | Col2 | Col3 |
        |------|------|------|
        | a    | b    | c    |
    """
    if not table or not table[0]:
        return ""

    # Clean None values
    cleaned = []
    for row in table:
        cleaned.append([str(cell).strip() if cell else "" for cell in row])

    # Header
    header = cleaned[0]
    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]

    # Data rows
    for row in cleaned[1:]:
        # Pad row if shorter than header
        padded = row + [""] * (len(header) - len(row))
        md_lines.append("| " + " | ".join(padded[: len(header)]) + " |")

    return "\n".join(md_lines)


def extract_text_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extract text from a PDF using PyMuPDF.

    Returns:
        List of dicts: [{"page": 1, "content": "...", "type": "text"}, ...]
    """
    pages = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:
                pages.append(
                    {
                        "page": page_num + 1,
                        "content": text,
                        "type": "text",
                    }
                )
        doc.close()
    except Exception as e:
        logger.error(f"PyMuPDF text extraction failed: {e}")
        raise

    return pages


def extract_tables_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extract tables from a PDF using pdfplumber and convert to Markdown.

    Each table is wrapped with contextual surrounding text from the page
    to provide context when retrieved during RAG.

    Returns:
        List of dicts: [{"page": 1, "content": "...", "type": "table"}, ...]
    """
    tables = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                if not page_tables:
                    continue

                # Get surrounding text for context
                page_text = page.extract_text() or ""
                # Take first 200 chars as context prefix
                context_prefix = page_text[:200].strip()

                for table_idx, table in enumerate(page_tables):
                    md_table = _table_to_markdown(table)
                    if not md_table:
                        continue

                    # Wrap table with context
                    content = (
                        f"[Context from page {page_num}]: {context_prefix}\n\n"
                        f"[Table {table_idx + 1} on page {page_num}]:\n"
                        f"{md_table}"
                    )
                    tables.append(
                        {
                            "page": page_num,
                            "content": content,
                            "type": "table",
                        }
                    )
    except Exception as e:
        logger.error(f"pdfplumber table extraction failed: {e}")
        raise

    return tables


def extract_all_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extract both text and tables from a PDF.

    Returns:
        Combined list of text and table segments, sorted by page number.
    """
    text_segments = extract_text_from_pdf(pdf_bytes)
    table_segments = extract_tables_from_pdf(pdf_bytes)

    # Combine and sort by page
    all_segments = text_segments + table_segments
    all_segments.sort(key=lambda x: (x["page"], 0 if x["type"] == "text" else 1))

    logger.info(
        f"Extracted {len(text_segments)} text segments and "
        f"{len(table_segments)} table segments from PDF"
    )
    return all_segments
