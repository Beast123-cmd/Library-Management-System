import asyncio
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.db.database import Base
from app.core.config import settings
from app.core.copies import add_copies
from app.models.models import Book, BookCopy, CopyStatus, HoldQueue, User, Transaction, TransactionStatus, AuditLog

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
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS copy_id INTEGER REFERENCES book_copies(id)",
            "CREATE INDEX IF NOT EXISTS ix_transactions_copy_id ON transactions (copy_id)",
        ):
            await conn.execute(text(statement))
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        books = (await db.execute(select(Book))).scalars().all()
        for book in books:
            copies = (await db.execute(
                select(BookCopy).where(BookCopy.book_id == book.id).order_by(BookCopy.copy_number)
            )).scalars().all()
            await add_copies(db, book, max(0, book.total_copies - len(copies)))
            await db.flush()
            copies = (await db.execute(
                select(BookCopy).where(BookCopy.book_id == book.id).order_by(BookCopy.copy_number)
            )).scalars().all()
            active_transactions = (await db.execute(
                select(Transaction).where(
                    Transaction.book_id == book.id,
                    Transaction.copy_id.is_(None),
                    Transaction.status.in_([TransactionStatus.issued, TransactionStatus.on_hold_shelf]),
                ).order_by(Transaction.id)
            )).scalars().all()
            if len(active_transactions) > len(copies):
                await add_copies(db, book, len(active_transactions) - len(copies))
                await db.flush()
                copies = (await db.execute(
                    select(BookCopy).where(BookCopy.book_id == book.id).order_by(BookCopy.copy_number)
                )).scalars().all()
                book.total_copies = len(copies)
            free_copies = [copy for copy in copies if copy.status == CopyStatus.available]
            for txn, copy in zip(active_transactions, free_copies):
                txn.copy_id = copy.id
                copy.status = CopyStatus.issued if txn.status == TransactionStatus.issued else CopyStatus.on_hold_shelf
            book.available_copies = sum(copy.status == CopyStatus.available for copy in copies)
        await db.commit()
        print("Migration complete!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
