import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.database import Base
import app.models.models  # Register every mapped table before create_all.


async def migrate():
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("-pooler", "")
    if "?" in db_url:
        base_url, query = db_url.split("?", 1)
        query = "&".join(item for item in query.split("&") if not item.startswith(("sslmode", "channel_binding")))
        db_url = f"{base_url}?{query}" if query else base_url
    engine = create_async_engine(db_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Fine payment table is ready.")


if __name__ == "__main__":
    asyncio.run(migrate())
