import unittest
from datetime import date, timedelta

from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.holds import place_hold
from app.api.v1.transactions import issue_book
from app.db.database import Base
from app.models.models import Book, BookCopy, CopyStatus, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus, User, UserRole
from app.schemas.schemas import TransactionCreate


class HoldWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_one_active_hold_until_collected(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            first = Book(title="First", author="Author", total_copies=1, available_copies=1)
            second = Book(title="Second", author="Author", total_copies=1, available_copies=1)
            db.add_all([admin, member, first, second])
            await db.flush()
            db.add_all([
                BookCopy(book_id=first.id, copy_number=1, accession_number="B1-0001"),
                BookCopy(book_id=second.id, copy_number=1, accession_number="B2-0001"),
            ])
            await db.commit()
            admin_id, member_id, first_id, second_id = admin.id, member.id, first.id, second.id

            hold = await place_hold(first.id, db, member)
            hold_id = hold.id
            self.assertEqual(first.available_copies, 0)
            self.assertIsNotNone(hold.expiration_date)
            shelf_copy_id = await db.scalar(select(Transaction.copy_id).where(Transaction.status == TransactionStatus.on_hold_shelf))
            self.assertEqual((await db.get(BookCopy, shelf_copy_id)).status, CopyStatus.on_hold_shelf)

            with self.assertRaises(HTTPException) as error:
                await place_hold(second.id, db, member)
            self.assertEqual(error.exception.status_code, 400)
            await db.rollback()
            self.assertEqual((await db.get(Book, second_id)).available_copies, 1)

            loan = await issue_book(
                TransactionCreate(user_id=member_id, book_id=first_id, expected_return_date=date.today() + timedelta(days=7)),
                db,
                await db.get(User, admin_id),
            )
            self.assertEqual(loan.status, TransactionStatus.issued)
            self.assertEqual((await db.get(BookCopy, shelf_copy_id)).status, CopyStatus.issued)
            self.assertEqual((await db.get(HoldQueue, hold_id)).status, HoldQueueStatus.fulfilled)

            next_hold = await place_hold(second_id, db, await db.get(User, member_id))
            self.assertEqual(next_hold.status, HoldQueueStatus.active)
            self.assertEqual((await db.get(Book, second_id)).available_copies, 0)


if __name__ == "__main__":
    unittest.main()
