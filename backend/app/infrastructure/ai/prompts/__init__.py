"""
Reusable prompt templates for the RAG pipeline.

All prompts are defined as ``ChatPromptTemplate`` objects so they can be
composed with LangChain Expression Language (LCEL) chains, tested in
isolation, and version-controlled independently of pipeline logic.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# ---------------------------------------------------------------------------
# Query Reformulation — used by create_history_aware_retriever
# ---------------------------------------------------------------------------
QUERY_REFORMULATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given a chat history and the latest user question which might "
            "reference context in the chat history, formulate a standalone "
            "question which can be understood without the chat history. "
            "Do NOT answer the question — just reformulate it if needed "
            "and otherwise return it as is.",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


# ---------------------------------------------------------------------------
# Generation — final answer synthesis with citation support
# ---------------------------------------------------------------------------
GENERATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an AI Librarian assistant. Answer the user's question "
            "based on the following context from {source_label}. "
            "Be accurate, helpful, and cite the context when applicable. "
            "If the context doesn't fully answer the question, say so clearly."
            "{citation_instruction}",
        ),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)


# ---------------------------------------------------------------------------
# Summarisation — sliding-window memory compression
# ---------------------------------------------------------------------------
SUMMARIZATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a summarization assistant. Condense the following "
            "conversation into a brief context summary that preserves "
            "the key information, questions asked, and answers given. "
            "Write in third person. Be concise but complete.",
        ),
        ("human", "{conversation}"),
    ]
)
