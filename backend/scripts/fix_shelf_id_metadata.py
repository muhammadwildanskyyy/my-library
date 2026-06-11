"""
Migration: Fix shelf_id metadata in langchain_pg_embedding.

Problem:
    Chunks ingested when shelf_id was None were stored with:
        cmetadata->>'shelf_id' = ''  (empty string)

    The retriever filter for shelf-scoped queries uses JSONB containment:
        cmetadata @> '{"shelf_id": "UUID_A"}'::jsonb

    This correctly excludes chunks with shelf_id="" when querying Rak A.
    BUT the retriever filter for library-wide queries (no shelf_id in filter)
    will INCLUDE chunks from ALL shelves including Rak B — which is correct.

    However, the real problem is the OPPOSITE: when a book belongs to Rak B
    and was ingested with shelf_id="UUID_B", querying Rak A should not return
    it. This is already handled correctly by JSONB containment.

    The cleanup needed: remove the empty shelf_id key from chunks that don't
    belong to any shelf, making the metadata clean and consistent with the
    new ingestion format (no shelf_id key when None).

Run this script against your PostgreSQL database:
    cd backend
    python -m scripts.fix_shelf_id_metadata

Or run the SQL directly:
    UPDATE langchain_pg_embedding
    SET cmetadata = cmetadata - 'shelf_id'
    WHERE cmetadata->>'shelf_id' = '';
"""

import asyncio
import logging
import sys
import os

# Add the backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_shelf_id_metadata(database_url: str) -> None:
    """Remove shelf_id key from chunks where it was stored as empty string."""
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # First: count affected rows
        count_result = await session.execute(
            text("""
                SELECT COUNT(*) 
                FROM langchain_pg_embedding 
                WHERE cmetadata->>'shelf_id' = ''
            """)
        )
        count = count_result.scalar()
        logger.info("Found %d chunks with empty shelf_id to clean up", count)

        if count == 0:
            logger.info("Nothing to fix. All good!")
            return

        # Fix: remove the shelf_id key from JSONB where it's an empty string
        result = await session.execute(
            text("""
                UPDATE langchain_pg_embedding
                SET cmetadata = cmetadata - 'shelf_id'
                WHERE cmetadata->>'shelf_id' = ''
            """)
        )
        await session.commit()

        updated = result.rowcount
        logger.info("✅ Fixed %d chunks — removed empty shelf_id key", updated)

    await engine.dispose()


async def main() -> None:
    from app.config.settings import get_settings
    s = get_settings()
    
    # Use the DATABASE_URL from settings
    db_url = s.DATABASE_URL
    logger.info("Connecting to: %s", db_url.split("@")[-1])  # Log without credentials
    
    await fix_shelf_id_metadata(db_url)


if __name__ == "__main__":
    asyncio.run(main())
