import unittest

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.books import update_copy_status
from app.db.database import Base
from app.models.models import Book, BookCopy, CopyStatus, User, UserRole
from app.schemas.schemas import CopyStatusUpdate


class InventoryAuditTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_damaged_copy_is_removed_from_available_count(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            book = Book(title="Book", author="Author", total_copies=1, available_copies=1)
            db.add_all([admin, book]); await db.flush()
            copy = BookCopy(book_id=book.id, copy_number=1, accession_number="B1-0001", status=CopyStatus.available)
            db.add(copy); await db.commit()
            result = await update_copy_status(copy.id, CopyStatusUpdate(status="damaged", note="Water damage"), db, admin)
            self.assertEqual(result["status"], "damaged")
            self.assertEqual(result["available_copies"], 0)


if __name__ == "__main__":
    unittest.main()
