import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.database import Base
from app.core.config import settings
from app.models.models import HoldQueue, User, Book, Transaction, AuditLog

async def migrate():
    # Schema changes need a direct Neon connection; the app uses the pooler.
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("-pooler", "")
    if "?" in db_url:
        base_url, query = db_url.split("?", 1)
        query = "&".join(part for part in query.split("&") if not part.startswith(("sslmode", "channel_binding")))
        db_url = f"{base_url}?{query}" if query else base_url
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        print("Running create_all to create new tables...")
        await conn.run_sync(Base.metadata.create_all)
        for statement in (
            "ALTER TABLE books ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
            "ALTER TABLE books ADD COLUMN IF NOT EXISTS language VARCHAR(100)",
            "ALTER TABLE books ADD COLUMN IF NOT EXISTS publisher VARCHAR(150)",
            "ALTER TABLE books ADD COLUMN IF NOT EXISTS edition VARCHAR(100)",
            "ALTER TABLE books ADD COLUMN IF NOT EXISTS shelf_location VARCHAR(100)",
            "CREATE INDEX IF NOT EXISTS ix_books_category ON books (category)",
            "CREATE INDEX IF NOT EXISTS ix_books_language ON books (language)",
            "CREATE INDEX IF NOT EXISTS ix_books_shelf_location ON books (shelf_location)",
        ):
            await conn.execute(text(statement))
        print("Migration complete!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
