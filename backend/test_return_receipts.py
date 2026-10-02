import unittest
from datetime import date, timedelta

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.transactions import get_return_receipt, return_book
from app.db.database import Base
from app.models.models import Book, BookCopy, CopyStatus, Transaction, TransactionStatus, User, UserRole
from app.schemas.schemas import ReturnRequest


class ReturnReceiptTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_waived_fine_receipt_is_saved_and_visible_to_borrower(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            borrower = User(name="Borrower", email="borrower@example.com", username="borrower", hashed_password="x")
            other = User(name="Other", email="other@example.com", username="other", hashed_password="x")
            book = Book(title="Book", author="Author", total_copies=1, available_copies=0)
            db.add_all([admin, borrower, other, book])
            await db.flush()
            copy = BookCopy(book_id=book.id, copy_number=1, accession_number=f"B{book.id}-0001", status=CopyStatus.issued)
            db.add(copy)
            await db.flush()
            loan = Transaction(
                user_id=borrower.id, book_id=book.id, issue_date=date.today() - timedelta(days=9),
                copy_id=copy.id, expected_return_date=date.today() - timedelta(days=2), status=TransactionStatus.issued,
            )
            db.add(loan)
            await db.commit()

            receipt = await return_book(loan.id, ReturnRequest(waive_fine=True, waiver_reason="Library closure"), db, admin)
            self.assertEqual(receipt.overdue_days, 2)
            self.assertEqual(receipt.assessed_fine, 10.0)
            self.assertEqual(receipt.fine_amount, 0.0)
            self.assertEqual(receipt.waiver_reason, "Library closure")
            self.assertTrue(receipt.waived)

            saved = await get_return_receipt(loan.id, db, borrower)
            self.assertEqual(saved.waiver_reason, "Library closure")
            self.assertEqual(saved.actual_return_date, date.today())
            with self.assertRaises(HTTPException) as error:
                await get_return_receipt(loan.id, db, other)
            self.assertEqual(error.exception.status_code, 404)

    def test_waiver_requires_a_reason(self):
        with self.assertRaises(ValidationError):
            ReturnRequest(waive_fine=True, waiver_reason="   ")


if __name__ == "__main__":
    unittest.main()
