import asyncio
from app.db.database import engine, Base
from app.models.models import HoldQueue, User, Book, Transaction, AuditLog

async def migrate():
    async with engine.begin() as conn:
        print("Running create_all to create new tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
