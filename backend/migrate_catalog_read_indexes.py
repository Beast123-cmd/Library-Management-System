"""Add read indexes used by the scaled catalogue filters and ordering.

Run from backend: venv/bin/python migrate_catalog_read_indexes.py
"""

import asyncio

from sqlalchemy import text

from app.db.database import engine


INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_books_catalog_title_id ON books (title, id)",
    "CREATE INDEX IF NOT EXISTS idx_books_available_title ON books (available_copies, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_category_title ON books (category, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_language_title ON books (language, title)",
    "CREATE INDEX IF NOT EXISTS idx_books_author_title ON books (author, title)",
)


async def main() -> None:
    async with engine.begin() as connection:
        for statement in INDEXES:
            await connection.execute(text(statement))
    await engine.dispose()
    print(f"Created or verified {len(INDEXES)} catalogue read indexes.")


if __name__ == "__main__":
    asyncio.run(main())
