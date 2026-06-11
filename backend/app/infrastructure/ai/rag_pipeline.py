"""
Corrective RAG Pipeline — LangGraph StateGraph with hybrid retrieval.

Architecture::

    1. RETRIEVE  → History-aware EnsembleRetriever + FlashrankRerank
    2. DECIDE    → Conditional edge: documents found? → generate : web_search
    3. WEB_SEARCH → Tavily fallback when local docs aren't found
    4. GENERATE  → LCEL chain with ChatPromptTemplate + StrOutputParser

Key improvements over v1:
- **No per-document LLM grading** — the FlashrankRerank cross-encoder
  handles relevance scoring more efficiently and accurately.
- **History-aware retrieval** — queries are automatically reformulated
  using conversational context before hitting the retriever.
- **EnsembleRetriever** — hybrid semantic + keyword search via
  Reciprocal Rank Fusion maximises recall.
- **Prompt templates** — managed as ``ChatPromptTemplate`` objects
  instead of inline dict construction.
- **LCEL chains** — generation uses ``prompt | llm | parser`` composition.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres import PGVector
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config.settings import Settings, get_settings
from app.domain.interfaces.ai_service import IWebSearchService
from app.infrastructure.ai.prompts import GENERATION_PROMPT
from app.infrastructure.ai.retriever_factory import build_full_retrieval_pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State schema for the RAG graph
# ---------------------------------------------------------------------------
class RAGState(TypedDict):
    """State passed between nodes in the Corrective RAG pipeline."""

    question: str
    chat_history: list[dict]        # [{role, content}, ...] conversation context
    documents: list[dict]           # Retrieved docs with metadata
    web_results: list[str]          # Web search fallback results
    generation: str                 # Final answer
    used_web: bool                  # Whether web search was triggered
    references: list[dict]          # Citation references for the answer


# ---------------------------------------------------------------------------
# Corrective RAG Pipeline
# ---------------------------------------------------------------------------
class CorrectiveRAGPipeline:
    """
    LangGraph-based Corrective RAG with hybrid retrieval, reranking,
    history-aware query reformulation, and web search fallback.

    Usage::

        pipeline = CorrectiveRAGPipeline(
            llm=chat_model,
            vector_store=pgvector_store,
            session_factory=async_session_factory,
            web_search_service=web_search,
        )
        result = await pipeline.run(
            question="What is X?",
            user_id="...",
            library_id=UUID("..."),
            chat_history=[{"role": "user", "content": "..."}],
        )
    """

    def __init__(
        self,
        llm: BaseChatModel,
        vector_store: PGVector,
        session_factory: async_sessionmaker,
        web_search_service: IWebSearchService,
        settings: Settings | None = None,
    ) -> None:
        self._llm = llm
        self._vector_store = vector_store
        self._session_factory = session_factory
        self._web_search = web_search_service
        self._settings = settings or get_settings()

        # Generation chain (LCEL): prompt → LLM → parse string
        self._generation_chain = GENERATION_PROMPT | self._llm | StrOutputParser()

        # Search scope — set before each run
        self._user_id: str = ""
        self._library_id: UUID = UUID(int=0)
        self._shelf_id: UUID | None = None

        # The retrieval pipeline is built per-run because it's scoped
        self._retriever: Any = None

        # Build the LangGraph state machine
        self._graph = self._build_graph()

    # ── Graph Construction ───────────────────────────────────────────────────
    def _build_graph(self) -> Any:
        graph = StateGraph(RAGState)

        # Add nodes
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("web_search", self._web_search_node)
        graph.add_node("generate", self._generate_node)

        # Set entry point
        graph.set_entry_point("retrieve")

        # Conditional edge: has documents → generate, else → web_search
        graph.add_conditional_edges(
            "retrieve",
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
        """
        Retrieve documents using the full hybrid pipeline.

        Steps (handled internally by the retriever chain):
        1. Reformulate query using chat history (history-aware)
        2. Ensemble search: PGVector semantic + PG Full-Text Search
        3. Rerank with FlashrankRerank cross-encoder
        4. Return top-N compressed documents
        """
        logger.info("[RAG] Retrieving docs for: %s…", state["question"][:80])

        # Convert chat history dicts to LangChain message objects
        lc_history = self._to_langchain_messages(state.get("chat_history", []))

        # Invoke the history-aware retrieval pipeline
        raw_docs: list[Document] = await self._retriever.ainvoke(
            {"input": state["question"], "chat_history": lc_history}
        )

        # Convert Document objects to dicts with metadata
        documents = []
        for doc in raw_docs:
            meta = doc.metadata or {}
            documents.append(
                {
                    "content": doc.page_content,
                    "book_id": meta.get("book_id", ""),
                    "book_title": meta.get("book_title", ""),
                    "filename": meta.get("filename", ""),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "source_type": meta.get("source_type", "text"),
                }
            )

        logger.info("[RAG] Retrieved %d documents after reranking", len(documents))
        return {"documents": documents}

    # ── Decision: Generate or Web Search ─────────────────────────────────────
    def _decide_source(self, state: RAGState) -> str:
        """Route to generate if we have docs, otherwise fall back to web."""
        if state.get("documents"):
            logger.info("[RAG] → Generating from %d retrieved documents", len(state["documents"]))
            return "generate"
        else:
            logger.info("[RAG] → No documents found, falling back to web search")
            return "web_search"

    # ── Node: Web Search ─────────────────────────────────────────────────────
    async def _web_search_node(self, state: RAGState) -> dict:
        """Search the web as a fallback when local docs aren't found."""
        logger.info("[RAG] Web searching: %s…", state["question"][:80])

        results = await self._web_search.search(state["question"])
        web_texts = [r["content"] for r in results if r.get("content")]

        logger.info("[RAG] Got %d web results", len(web_texts))
        return {"web_results": web_texts, "used_web": True}

    # ── Node: Generate ───────────────────────────────────────────────────────
    async def _generate_node(self, state: RAGState) -> dict:
        """
        Generate the final answer using LCEL chain with citation markers.

        Uses ``GENERATION_PROMPT | LLM | StrOutputParser()`` composition.
        """
        documents = state.get("documents", [])
        web_parts = state.get("web_results", [])
        references: list[dict] = []

        if documents:
            # Build numbered context with citation markers
            context_parts = []
            for idx, doc in enumerate(documents, start=1):
                ref_marker = f"[{idx}]"
                source_info = (
                    f'(Sumber: "{doc["book_title"]}", '
                    f'Bagian ke-{doc["chunk_index"] + 1})'
                )
                context_parts.append(f"{ref_marker} {source_info}\n{doc['content']}")

                references.append(
                    {
                        "ref_index": idx,
                        "book_id": doc["book_id"],
                        "book_title": doc["book_title"],
                        "filename": doc["filename"],
                        "chunk_index": doc["chunk_index"],
                        "source_type": doc["source_type"],
                    }
                )

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

        # Convert chat history for the prompt
        lc_history = self._to_langchain_messages(state.get("chat_history", []))

        # Invoke LCEL generation chain
        generation = await self._generation_chain.ainvoke(
            {
                "source_label": source_label,
                "citation_instruction": citation_instruction,
                "chat_history": lc_history,
                "context": context,
                "question": state["question"],
            }
        )

        used_web = state.get("used_web", False)
        logger.info(
            "[RAG] Generated answer (%d chars, web=%s, references=%d)",
            len(generation),
            "yes" if used_web else "no",
            len(references),
        )

        return {
            "generation": generation,
            "used_web": used_web,
            "references": references,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _to_langchain_messages(
        chat_history: list[dict],
    ) -> list[HumanMessage | AIMessage]:
        """Convert chat history dicts to LangChain message objects."""
        messages: list[HumanMessage | AIMessage] = []
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        return messages

    # ── Public API ───────────────────────────────────────────────────────────
    async def run(
        self,
        question: str,
        user_id: str,
        library_id: UUID,
        shelf_id: UUID | None = None,
        chat_history: list[dict] | None = None,
    ) -> dict:
        """
        Execute the full Corrective RAG pipeline.

        Args:
            question: The user's query.
            user_id: Current user ID (for pre-filtering).
            library_id: Library scope (for pre-filtering).
            shelf_id: Optional shelf scope.
            chat_history: Conversation history as list of {role, content} dicts.

        Returns:
            Dict with 'answer', 'used_web', 'references',
            'num_docs_retrieved'.
        """
        # Set search scope
        self._user_id = user_id
        self._library_id = library_id
        self._shelf_id = shelf_id

        # Build scoped retrieval pipeline for this request
        self._retriever = build_full_retrieval_pipeline(
            llm=self._llm,
            vector_store=self._vector_store,
            session_factory=self._session_factory,
            user_id=user_id,
            library_id=library_id,
            shelf_id=shelf_id,
            settings=self._settings,
        )

        # Initial state
        initial_state: RAGState = {
            "question": question,
            "chat_history": chat_history or [],
            "documents": [],
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
            "num_docs_relevant": len(result.get("documents", [])),
        }
