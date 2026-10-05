import unittest
from datetime import date

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.dashboard import get_dashboard_stats
from app.db.database import Base
from app.models.models import Book, FinePayment, Transaction, TransactionStatus, User, UserRole


class DashboardFineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_dashboard_reports_only_unpaid_fines(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            book = Book(title="Book", author="Author")
            db.add_all([admin, member, book]); await db.flush()
            paid = Transaction(user_id=member.id, book_id=book.id, issue_date=date.today(), expected_return_date=date.today(), actual_return_date=date.today(), status=TransactionStatus.returned, fine_amount=100)
            unpaid = Transaction(user_id=member.id, book_id=book.id, issue_date=date.today(), expected_return_date=date.today(), actual_return_date=date.today(), status=TransactionStatus.returned, fine_amount=40)
            db.add_all([paid, unpaid]); await db.flush()
            db.add(FinePayment(transaction_id=paid.id, amount=75, received_by_id=admin.id))
            await db.commit()
            stats = await get_dashboard_stats(db, admin)
            self.assertEqual(stats["kpis"]["outstanding_fines"], 65.0)


if __name__ == "__main__":
    unittest.main()
