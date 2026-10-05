"""Add read indexes used by the scaled catalogue filters and ordering.

Run from backend: venv/bin/python migrate_catalog_read_indexes.py
"""

import asyncio

from sqlalchemy import text

from app.db.database import engine


INDEXES = (
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "CREATE INDEX IF NOT EXISTS idx_books_catalog_title_id ON books (title, id)",
    "CREATE INDEX IF NOT EXISTS idx_books_available_title ON books (available_copies, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_category_title ON books (category, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_language_title ON books (language, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_author_title ON books (author, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_title_trgm ON books USING gin (title gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_books_author_trgm ON books USING gin (author gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_books_isbn_trgm ON books USING gin (isbn gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_books_publisher_trgm ON books USING gin (publisher gin_trgm_ops)",
)


async def main() -> None:
    async with engine.begin() as connection:
        for statement in INDEXES:
            await connection.execute(text(statement))
    await engine.dispose()
    print(f"Created or verified {len(INDEXES)} catalogue read indexes.")


if __name__ == "__main__":
    asyncio.run(main())
