import unittest
from datetime import date

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.analytics import get_analytics_stats
from app.db.database import Base
from app.models.models import Book, Transaction, TransactionStatus, User, UserRole


class AnalyticsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_stats_include_uncategorized_books_without_query_failure(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            categorized = Book(title="Fiction", author="Author", category="Fiction")
            uncategorized = Book(title="Untitled", author="Author")
            db.add_all([admin, member, categorized, uncategorized]); await db.flush()
            db.add(Transaction(user_id=member.id, book_id=categorized.id, issue_date=date.today(), expected_return_date=date.today(), status=TransactionStatus.issued))
            await db.commit()
            stats = await get_analytics_stats(days=180, db=db, _=admin)
            self.assertEqual(sum(item["value"] for item in stats["categoryData"]), 100.0)
            self.assertIn("Uncategorized", [item["name"] for item in stats["categoryData"]])
            self.assertEqual(stats["topBooksData"][0]["name"], "Fiction")


if __name__ == "__main__":
    unittest.main()
