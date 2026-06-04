"""
Dynamic LLM Factory — returns the correct ChatModel based on ACTIVE_MODEL setting.

The service layer calls `create_chat_model()` and receives a LangChain
BaseChatModel without knowing whether it's OpenAI or Gemini.
"""

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.config.settings import Settings, get_settings


def create_chat_model(settings: Settings | None = None) -> BaseChatModel:
    """
    Create a LangChain chat model based on the ACTIVE_MODEL environment variable.

    Returns:
        BaseChatModel — either ChatOpenAI or ChatGoogleGenerativeAI.

    Raises:
        ValueError: If ACTIVE_MODEL is not 'openai' or 'gemini'.
    """
    s = settings or get_settings()

    if s.ACTIVE_MODEL == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=s.OPENAI_API_KEY,  # type: ignore[arg-type]
            temperature=0.1,
            max_tokens=2048,
        )
    elif s.ACTIVE_MODEL == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=s.GOOGLE_API_KEY,  # type: ignore[arg-type]
            temperature=0.1,
            max_output_tokens=2048,
        )
    else:
        raise ValueError(
            f"Unknown ACTIVE_MODEL '{s.ACTIVE_MODEL}'. Expected 'openai' or 'gemini'."
        )
