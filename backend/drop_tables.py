import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ASYNC_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
if "?" in ASYNC_URL:
    base_url, query = ASYNC_URL.split("?", 1)
    params = query.split("&")
    clean_params = [p for p in params if not p.startswith("sslmode") and not p.startswith("channel_binding")]
    if clean_params:
        ASYNC_URL = base_url + "?" + "&".join(clean_params)
    else:
        ASYNC_URL = base_url

async def main():
    engine = create_async_engine(ASYNC_URL, echo=True)
    async with engine.begin() as conn:
        print("💥 Dropping old tables to avoid conflicts...")
        await conn.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS books CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        print("💥 Dropping old flask tables...")
        await conn.execute(text("DROP TABLE IF EXISTS books_new CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS members CASCADE;"))
        print("✅ Drop completed!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
