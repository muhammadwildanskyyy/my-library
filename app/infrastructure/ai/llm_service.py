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
        return str(response.content)

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
