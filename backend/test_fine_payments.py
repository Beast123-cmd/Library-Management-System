import unittest
from datetime import date

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.transactions import record_fine_payment
from app.db.database import Base
from app.models.models import Book, Transaction, TransactionStatus, User, UserRole
from app.schemas.schemas import FinePaymentCreate


class FinePaymentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_payment_tracks_the_remaining_balance_and_rejects_overpayment(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            book = Book(title="Book", author="Author")
            db.add_all([admin, member, book])
            await db.flush()
            transaction = Transaction(user_id=member.id, book_id=book.id, issue_date=date.today(), expected_return_date=date.today(), actual_return_date=date.today(), status=TransactionStatus.returned, fine_amount=25.0)
            db.add(transaction)
            await db.commit()

            record = await record_fine_payment(transaction.id, FinePaymentCreate(amount=10), db, admin)
            self.assertEqual(record.paid_amount, 10.0)
            self.assertEqual(record.outstanding_amount, 15.0)
            with self.assertRaises(HTTPException) as error:
                await record_fine_payment(transaction.id, FinePaymentCreate(amount=16), db, admin)
            self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
