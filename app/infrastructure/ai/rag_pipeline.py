"""
Corrective RAG Pipeline — LangGraph StateGraph implementation.

Flow:
  1. RETRIEVE  → pgvector similarity search (pre-filtered by hierarchy)
  2. GRADE     → LLM evaluates each document's relevance to the query
  3. DECIDE    → Conditional edge: relevant docs exist? → generate : web_search
  4. WEB_SEARCH → Tavily fallback when local docs aren't relevant
  5. GENERATE  → LLM synthesizes final answer from relevant context

This design ensures:
  - Only relevant documents reach the generation step
  - Web search fills gaps when the knowledge base lacks coverage
  - Context isolation is preserved by pre-filtering at the retrieve step
  - Citations/references link generated answers back to source documents
"""

import logging
from typing import Any, TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph

from app.domain.interfaces.ai_service import IEmbeddingService, ILLMService, IWebSearchService
from app.domain.interfaces.chunk_repository import IChunkRepository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State schema for the RAG graph
# ---------------------------------------------------------------------------
class RAGState(TypedDict):
    """State passed between nodes in the Corrective RAG pipeline."""

    question: str
    context_messages: str        # Serialized conversation context
    documents: list[dict]        # Retrieved docs with metadata
    relevant_docs: list[dict]    # Documents that passed grading
    web_results: list[str]       # Web search fallback results
    generation: str              # Final answer
    used_web: bool               # Whether web search was triggered
    references: list[dict]       # Citation references for the answer


# ---------------------------------------------------------------------------
# Corrective RAG Pipeline
# ---------------------------------------------------------------------------
class CorrectiveRAGPipeline:
    """
    LangGraph-based Corrective RAG with document grading, web search fallback,
    and inline citation references.

    Usage:
        pipeline = CorrectiveRAGPipeline(
            llm_service, embedding_service, chunk_repo, web_search_service
        )
        result = await pipeline.run(
            question="What is X?",
            user_id="...", library_id=UUID("..."),
            context_messages="Previous conversation..."
        )
    """

    def __init__(
        self,
        llm_service: ILLMService,
        embedding_service: IEmbeddingService,
        chunk_repo: IChunkRepository,
        web_search_service: IWebSearchService,
    ) -> None:
        self._llm = llm_service
        self._embedder = embedding_service
        self._chunk_repo = chunk_repo
        self._web_search = web_search_service

        # Search scope — set before each run
        self._user_id: str = ""
        self._library_id: UUID = UUID(int=0)
        self._shelf_id: UUID | None = None
        self._top_k: int = 5

        # Build the graph
        self._graph = self._build_graph()

    # ── Graph Construction ───────────────────────────────────────────────────
    def _build_graph(self) -> StateGraph:
        graph = StateGraph(RAGState)

        # Add nodes
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("grade_documents", self._grade_node)
        graph.add_node("web_search", self._web_search_node)
        graph.add_node("generate", self._generate_node)

        # Set entry point
        graph.set_entry_point("retrieve")

        # Edges
        graph.add_edge("retrieve", "grade_documents")
        graph.add_conditional_edges(
            "grade_documents",
            self._decide_source,
            {
                "generate": "generate",
                "web_search": "web_search",
            },
        )
        graph.add_edge("web_search", "generate")
        graph.add_edge("generate", END)

        return graph.compile()

    # ── Node: Retrieve ───────────────────────────────────────────────────────
    async def _retrieve_node(self, state: RAGState) -> dict:
        """Retrieve relevant chunks from pgvector with pre-filtering and metadata."""
        logger.info(f"[RAG] Retrieving docs for: {state['question'][:80]}...")

        # Embed the query
        query_embedding = await self._embedder.embed_query(state["question"])

        # Similarity search with metadata (JOIN to books table)
        chunks = await self._chunk_repo.similarity_search_with_metadata(
            query_embedding=query_embedding,
            user_id=self._user_id,
            library_id=self._library_id,
            shelf_id=self._shelf_id,
            top_k=self._top_k,
        )

        # Build document dicts with content + metadata
        documents = [
            {
                "content": chunk.content,
                "book_id": str(chunk.book_id),
                "book_title": chunk.book_title,
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
                "source_type": chunk.source_type,
            }
            for chunk in chunks
        ]
        logger.info("Retrieved chunks: %s", documents)
        logger.info(f"[RAG] Retrieved {len(documents)} documents")
        logger.info("Retrieved chunks: %s", documents)
        return {"documents": documents}

    # ── Node: Grade Documents ────────────────────────────────────────────────
    async def _grade_node(self, state: RAGState) -> dict:
        """Use LLM to grade each document for relevance to the question."""
        logger.info(f"[RAG] Grading {len(state['documents'])} documents")

        if not state["documents"]:
            return {"relevant_docs": []}

        relevant = []
        for doc in state["documents"]:
            grade = await self._grade_single_document(
                state["question"], doc["content"]
            )
            if grade:
                relevant.append(doc)

        logger.info(
            f"[RAG] {len(relevant)}/{len(state['documents'])} documents relevant"
        )
        return {"relevant_docs": relevant}

    async def _grade_single_document(self, question: str, document: str) -> bool:
        """Grade a single document — returns True if relevant."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a document relevance grader. "
                    "Determine if the document contains information relevant "
                    "to answering the user's question. "
                    "You MUST respond with ONLY a single word: 'yes' or 'no'. "
                    "Do not add any explanation."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Document:\n{document[:2000]}\n\n"
                    "Is this document relevant to the question? Answer with only 'yes' or 'no'."
                ),
            },
        ]
        response = await self._llm.generate(messages)
        cleaned = response.strip().lower().replace("*", "").replace(".", "")
        logger.info(f"[RAG] Grader raw response: '{response.strip()}' → cleaned: '{cleaned}'")

        # Accept 'yes' or 'ya' (Indonesian) anywhere in the response
        is_relevant = "yes" in cleaned or "ya" in cleaned
        return is_relevant

    # ── Decision: Generate or Web Search ─────────────────────────────────────
    def _decide_source(self, state: RAGState) -> str:
        """Decide whether to generate from docs or fall back to web search."""
        if state.get("relevant_docs"):
            logger.info("[RAG] → Generating from relevant documents")
            return "generate"
        else:
            logger.info("[RAG] → No relevant docs, falling back to web search")
            return "web_search"

    # ── Node: Web Search ─────────────────────────────────────────────────────
    async def _web_search_node(self, state: RAGState) -> dict:
        """Search the web as a fallback when local docs aren't relevant."""
        logger.info(f"[RAG] Web searching: {state['question'][:80]}...")

        results = await self._web_search.search(state["question"])
        web_texts = [r["content"] for r in results if r.get("content")]

        logger.info(f"[RAG] Got {len(web_texts)} web results")
        return {"web_results": web_texts, "used_web": True}

    # ── Node: Generate ───────────────────────────────────────────────────────
    async def _generate_node(self, state: RAGState) -> dict:
        """Generate the final answer using relevant context with citation markers."""
        # Build context from relevant docs or web results
        relevant = state.get("relevant_docs", [])
        web_parts = state.get("web_results", [])
        references: list[dict] = []

        if relevant:
            # Build numbered context with citation markers
            context_parts = []
            for idx, doc in enumerate(relevant, start=1):
                ref_marker = f"[{idx}]"
                source_info = f'(Sumber: "{doc["book_title"]}", Bagian ke-{doc["chunk_index"] + 1})'
                context_parts.append(
                    f"{ref_marker} {source_info}\n{doc['content']}"
                )
                # Build reference entry
                references.append({
                    "ref_index": idx,
                    "book_id": doc["book_id"],
                    "book_title": doc["book_title"],
                    "filename": doc["filename"],
                    "chunk_index": doc["chunk_index"],
                    "source_type": doc["source_type"],
                })

            context = "\n\n---\n\n".join(context_parts)
            source_label = "your knowledge base"
            citation_instruction = (
                "\n\nIMPORTANT: When using information from the context, "
                "you MUST cite the source by including the reference number "
                "in square brackets (e.g., [1], [2]) inline within your answer. "
                "Place the citation immediately after the relevant sentence or claim. "
                "Only cite references that you actually use."
            )
        elif web_parts:
            context = "\n\n---\n\n".join(web_parts)
            source_label = "web search results"
            citation_instruction = ""
        else:
            context = "No relevant information found."
            source_label = "no available sources"
            citation_instruction = ""

        # Include conversation context if available
        conversation_context = state.get("context_messages", "")
        conversation_section = ""
        if conversation_context:
            conversation_section = (
                f"\n\nPrevious conversation context:\n{conversation_context}\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI Librarian assistant. Answer the user's question "
                    f"based on the following context from {source_label}. "
                    "Be accurate, helpful, and cite the context when applicable. "
                    "If the context doesn't fully answer the question, say so clearly."
                    f"{citation_instruction}"
                    f"{conversation_section}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context}\n\n"
                    f"Question: {state['question']}"
                ),
            },
        ]

        generation = await self._llm.generate(messages)
        used_web = state.get("used_web", False)

        logger.info(
            f"[RAG] Generated answer ({len(generation)} chars, "
            f"web={'yes' if used_web else 'no'}, "
            f"references={len(references)})"
        )
        return {
            "generation": generation,
            "used_web": used_web,
            "references": references,
        }

    # ── Public API ───────────────────────────────────────────────────────────
    async def run(
        self,
        question: str,
        user_id: str,
        library_id: UUID,
        shelf_id: UUID | None = None,
        top_k: int = 5,
        context_messages: str = "",
    ) -> dict:
        """
        Execute the full Corrective RAG pipeline.

        Args:
            question: The user's query.
            user_id: Current user ID (for pre-filtering).
            library_id: Library scope (for pre-filtering).
            shelf_id: Optional shelf scope.
            top_k: Number of chunks to retrieve.
            context_messages: Serialized conversation context.

        Returns:
            Dict with 'answer', 'used_web', 'references',
            'num_docs_retrieved', 'num_docs_relevant'.
        """
        # Set search scope
        self._user_id = user_id
        self._library_id = library_id
        self._shelf_id = shelf_id
        self._top_k = top_k

        # Initial state
        initial_state: RAGState = {
            "question": question,
            "context_messages": context_messages,
            "documents": [],
            "relevant_docs": [],
            "web_results": [],
            "generation": "",
            "used_web": False,
            "references": [],
        }

        # Run the graph
        result = await self._graph.ainvoke(initial_state)

        return {
            "answer": result.get("generation", ""),
            "used_web": result.get("used_web", False),
            "references": result.get("references", []),
            "num_docs_retrieved": len(result.get("documents", [])),
            "num_docs_relevant": len(result.get("relevant_docs", [])),
        }
