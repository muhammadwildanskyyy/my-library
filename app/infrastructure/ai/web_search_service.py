"""
Concrete implementation of IWebSearchService using Tavily.

Used by the Corrective RAG pipeline when retrieved documents
are not relevant to the query.
"""

from tavily import AsyncTavilyClient

from app.config.settings import Settings, get_settings
from app.domain.interfaces.ai_service import IWebSearchService


class WebSearchService(IWebSearchService):
    """Web search fallback using Tavily API."""

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self._client = AsyncTavilyClient(api_key=s.TAVILY_API_KEY)

    async def search(self, query: str) -> list[dict]:
        """
        Search the web for the given query.

        Returns:
            List of dicts with 'content' and 'url' keys.
        """
        response = await self._client.search(
            query=query,
            search_depth="basic",
            max_results=5,
        )

        results = []
        for item in response.get("results", []):
            results.append(
                {
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                }
            )
        return results
