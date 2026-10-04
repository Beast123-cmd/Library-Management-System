import unittest
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.dashboard import get_work_queue
from app.db.database import Base
from app.models.models import Book, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus, User, UserRole


class DashboardWorkQueueTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_queue_groups_only_open_loans_and_active_pickups(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            book = Book(title="Queue Book", author="Author", total_copies=2, available_copies=0)
            db.add_all([admin, member, book])
            await db.flush()

            db.add_all([
                Transaction(user_id=member.id, book_id=book.id, issue_date=date.today(), expected_return_date=date.today(), status=TransactionStatus.issued),
                Transaction(user_id=member.id, book_id=book.id, issue_date=date.today() - timedelta(days=3), expected_return_date=date.today() - timedelta(days=1), status=TransactionStatus.issued),
                Transaction(user_id=member.id, book_id=book.id, issue_date=date.today(), expected_return_date=date.today(), actual_return_date=date.today(), status=TransactionStatus.returned),
                HoldQueue(user_id=member.id, book_id=book.id, status=HoldQueueStatus.active, expiration_date=datetime.now() + timedelta(hours=4)),
                HoldQueue(user_id=member.id, book_id=book.id, status=HoldQueueStatus.cancelled),
            ])
            await db.commit()

            queue = await get_work_queue(db, admin)

            self.assertEqual(len(queue["due_today"]), 1)
            self.assertEqual(len(queue["overdue"]), 1)
            self.assertEqual(len(queue["ready_for_pickup"]), 1)
            self.assertEqual(queue["due_today"][0]["book_title"], "Queue Book")


if __name__ == "__main__":
    unittest.main()
