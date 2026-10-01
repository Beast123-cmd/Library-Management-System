import unittest
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.transactions import return_book
from app.db.database import Base
from app.models.models import (
    Book,
    HoldQueue,
    HoldQueueStatus,
    Transaction,
    TransactionStatus,
    User,
    UserRole,
)
from app.schemas.schemas import ReturnRequest


class HoldReturnTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def seed(self, with_shelf_copy):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            book = Book(title="Test Book", author="Author", total_copies=2 if with_shelf_copy else 1, available_copies=0)
            db.add_all([admin, member, book])
            await db.flush()
            issued = Transaction(
                user_id=admin.id, book_id=book.id, issue_date=date.today(),
                expected_return_date=date.today() + timedelta(days=7), status=TransactionStatus.issued,
            )
            hold = HoldQueue(
                user_id=member.id, book_id=book.id, status=HoldQueueStatus.active,
                expiration_date=datetime.now(timezone.utc) + timedelta(hours=12) if with_shelf_copy else None,
            )
            db.add_all([issued, hold])
            if with_shelf_copy:
                db.add(Transaction(
                    user_id=member.id, book_id=book.id, issue_date=date.today(),
                    expected_return_date=date.today(), status=TransactionStatus.on_hold_shelf,
                ))
            await db.commit()
            return admin.id, book.id, issued.id, hold.id

    async def test_return_does_not_duplicate_an_existing_shelf_copy(self):
        admin_id, book_id, issued_id, _ = await self.seed(with_shelf_copy=True)
        async with self.sessions() as db:
            admin = await db.get(User, admin_id)
            await return_book(issued_id, ReturnRequest(), db, admin)
            shelf_count = await db.scalar(select(func.count()).select_from(Transaction).where(
                Transaction.book_id == book_id,
                Transaction.status == TransactionStatus.on_hold_shelf,
            ))
            book = await db.get(Book, book_id)
            self.assertEqual(shelf_count, 1)
            self.assertEqual(book.available_copies, 1)

    async def test_waiting_hold_gets_returned_copy_for_twelve_hours(self):
        admin_id, book_id, issued_id, hold_id = await self.seed(with_shelf_copy=False)
        async with self.sessions() as db:
            admin = await db.get(User, admin_id)
            await return_book(issued_id, ReturnRequest(), db, admin)
            hold = await db.get(HoldQueue, hold_id)
            shelf_count = await db.scalar(select(func.count()).select_from(Transaction).where(
                Transaction.book_id == book_id,
                Transaction.status == TransactionStatus.on_hold_shelf,
            ))
            book = await db.get(Book, book_id)
            expiry = hold.expiration_date.replace(tzinfo=timezone.utc)
            self.assertAlmostEqual((expiry - datetime.now(timezone.utc)).total_seconds(), 12 * 3600, delta=10)
            self.assertEqual(shelf_count, 1)
            self.assertEqual(book.available_copies, 0)

    async def test_shelf_copy_cannot_be_returned_as_a_loan(self):
        admin_id, book_id, _, _ = await self.seed(with_shelf_copy=True)
        async with self.sessions() as db:
            admin = await db.get(User, admin_id)
            shelf_id = await db.scalar(select(Transaction.id).where(
                Transaction.book_id == book_id,
                Transaction.status == TransactionStatus.on_hold_shelf,
            ))
            with self.assertRaises(HTTPException) as error:
                await return_book(shelf_id, ReturnRequest(), db, admin)
            self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
