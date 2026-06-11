"""
Optional LLM response caching.

When enabled, identical LLM calls (same messages) return cached responses
instantly without hitting the provider API.  This saves cost and reduces
latency for repeated queries.

Enable via ``ENABLE_LLM_CACHE=true`` in environment / settings.
"""

from __future__ import annotations

import logging

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def setup_llm_cache(settings: Settings | None = None) -> None:
    """
    Configure LangChain's global LLM cache if enabled in settings.

    Uses ``InMemoryCache`` — suitable for single-process deployments.
    For multi-process / distributed setups, swap with a Redis or
    PostgreSQL-backed cache.
    """
    s = settings or get_settings()

    if not s.ENABLE_LLM_CACHE:
        logger.info("[Cache] LLM caching is DISABLED")
        return

    from langchain_core.caches import InMemoryCache
    from langchain_core.globals import set_llm_cache

    set_llm_cache(InMemoryCache())
    logger.info("[Cache] LLM caching ENABLED (InMemoryCache)")
