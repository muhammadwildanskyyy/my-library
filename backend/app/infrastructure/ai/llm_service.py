"""
Concrete implementation of ILLMService using the dynamic LLM factory.
"""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.domain.interfaces.ai_service import ILLMService
from app.infrastructure.ai.llm_factory import create_chat_model


class LLMService(ILLMService):
    """LLM text generation using the active model from settings."""

    def __init__(self) -> None:
        self._llm = create_chat_model()

    @staticmethod
    def _to_langchain_messages(messages: list[dict]) -> list:
        """Convert dict messages to LangChain message objects."""
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))
        return lc_messages

    async def generate(self, messages: list[dict]) -> str:
        """Generate a response from a list of message dicts."""
        lc_messages = self._to_langchain_messages(messages)
        response = await self._llm.ainvoke(lc_messages)
        
        content = response.content
        
        # LangChain Gemini models sometimes return content as a list of parts,
        # or a string representation of a list of parts.
        import ast
        if isinstance(content, str) and content.strip().startswith("[") and content.strip().endswith("]"):
            try:
                # Safely evaluate string representation of a list
                parsed = ast.literal_eval(content.strip())
                if isinstance(parsed, list):
                    content = parsed
            except (ValueError, SyntaxError):
                pass

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(str(part["text"]))
                else:
                    text_parts.append(str(part))
            return " ".join(text_parts).strip()
            
        return str(content).strip()

    async def summarize(self, messages: list[dict]) -> str:
        """Summarize a list of messages into a concise context string."""
        summary_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a summarization assistant. Condense the following "
                    "conversation into a brief context summary that preserves "
                    "the key information, questions asked, and answers given. "
                    "Write in third person. Be concise but complete."
                ),
            },
            {
                "role": "user",
                "content": "\n".join(
                    f"{m['role'].upper()}: {m['content']}" for m in messages
                ),
            },
        ]
        return await self.generate(summary_prompt)

    async def generate_session_title(self, question: str, context: str) -> str:
        """Generate a short title for a chat session based on question and context."""
        title_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Generate a very short title "
                    "(maximum 3-4 words) for a chat session based on the user's "
                    "first question and the context of the answer. "
                    "Return ONLY the title text, with no quotes or extra words."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\nContext: {context}",
            },
        ]
        title = await self.generate(title_prompt)
        return title.strip('"\' ')
