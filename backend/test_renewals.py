import unittest
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.transactions import list_transactions, renew_loan
from app.db.database import Base
from app.models.models import Book, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus, User


class RenewalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def seed(self, due_date=None):
        async with self.sessions() as db:
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            other = User(name="Other", email="other@example.com", username="other", hashed_password="x")
            book = Book(title="Book", author="Author", total_copies=2, available_copies=1)
            db.add_all([member, other, book])
            await db.flush()
            txn = Transaction(
                user_id=member.id, book_id=book.id, issue_date=date.today(),
                expected_return_date=due_date or date.today() + timedelta(days=2),
                status=TransactionStatus.issued,
            )
            db.add(txn)
            await db.commit()
            return member.id, other.id, book.id, txn.id

    async def test_member_can_renew_once_and_see_updated_loan(self):
        member_id, _, book_id, txn_id = await self.seed()
        async with self.sessions() as db:
            member = await db.get(User, member_id)
            renewed = await renew_loan(txn_id, db, member)
            self.assertEqual(renewed.expected_return_date, date.today() + timedelta(days=9))
            self.assertEqual(renewed.renewal_count, 1)

            db.add(Transaction(
                user_id=member_id, book_id=book_id, issue_date=date.today(),
                expected_return_date=date.today(), status=TransactionStatus.on_hold_shelf,
            ))
            await db.commit()
            loans = await list_transactions(1, 20, None, None, db, member)
            self.assertEqual(loans.total, 1)
            self.assertEqual(loans.data[0].renewal_count, 1)

            with self.assertRaises(HTTPException) as error:
                await renew_loan(txn_id, db, member)
            self.assertEqual(error.exception.status_code, 400)

    async def test_other_member_and_overdue_loan_cannot_be_renewed(self):
        member_id, other_id, _, txn_id = await self.seed(date.today() - timedelta(days=1))
        async with self.sessions() as db:
            with self.assertRaises(HTTPException) as other_error:
                await renew_loan(txn_id, db, await db.get(User, other_id))
            self.assertEqual(other_error.exception.status_code, 404)
            with self.assertRaises(HTTPException) as overdue_error:
                await renew_loan(txn_id, db, await db.get(User, member_id))
            self.assertEqual(overdue_error.exception.status_code, 400)

    async def test_another_members_hold_blocks_renewal(self):
        member_id, other_id, book_id, txn_id = await self.seed()
        async with self.sessions() as db:
            db.add(HoldQueue(
                user_id=other_id, book_id=book_id, status=HoldQueueStatus.active,
                expiration_date=datetime.now(timezone.utc) + timedelta(hours=2),
            ))
            await db.commit()
            with self.assertRaises(HTTPException) as error:
                await renew_loan(txn_id, db, await db.get(User, member_id))
            self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
