import unittest
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.notifications import get_notifications
from app.db.database import Base
from app.models.models import Book, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus, User


class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_returns_enabled_due_overdue_and_hold_alerts(self):
        async with self.sessions() as db:
            user = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            book = Book(title="Book", author="Author")
            db.add_all([user, book]); await db.flush()
            db.add_all([
                Transaction(user_id=user.id, book_id=book.id, issue_date=date.today(), expected_return_date=date.today() - timedelta(days=1), status=TransactionStatus.issued),
                HoldQueue(user_id=user.id, book_id=book.id, status=HoldQueueStatus.active, expiration_date=datetime.now(timezone.utc) + timedelta(hours=2)),
            ])
            await db.commit()
            alerts = await get_notifications(db, user)
            self.assertEqual({alert["type"] for alert in alerts}, {"overdue", "hold"})


if __name__ == "__main__":
    unittest.main()
