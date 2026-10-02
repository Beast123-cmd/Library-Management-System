import unittest
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.books import create_book, list_book_copies
from app.api.v1.transactions import issue_book, return_book
from app.db.database import Base
from app.models.models import BookCopy, CopyStatus, User, UserRole
from app.schemas.schemas import BookCreate, ReturnRequest, TransactionCreate, TransactionOut


class BookCopyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_copy_is_created_issued_and_returned(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            db.add_all([admin, member])
            await db.commit()

            book = await create_book(BookCreate(title="Book", author="Author", total_copies=2), db, admin)
            copies = await list_book_copies(book.id, db, admin)
            self.assertEqual([copy.accession_number for copy in copies], [f"B{book.id}-0001", f"B{book.id}-0002"])

            loan = await issue_book(
                TransactionCreate(user_id=member.id, book_id=book.id, expected_return_date=date.today() + timedelta(days=7)),
                db,
                admin,
            )
            self.assertEqual(loan.copy.accession_number, f"B{book.id}-0001")
            self.assertEqual(TransactionOut.model_validate(loan).model_dump(by_alias=True)["copy"]["accession_number"], f"B{book.id}-0001")
            issued_copy = await db.get(BookCopy, loan.copy_id)
            self.assertEqual(issued_copy.status, CopyStatus.issued)

            await return_book(loan.id, ReturnRequest(), db, admin)
            returned_copy = await db.get(BookCopy, loan.copy_id)
            self.assertEqual(returned_copy.status, CopyStatus.available)
            self.assertEqual(len((await db.execute(select(BookCopy).where(BookCopy.book_id == book.id))).scalars().all()), 2)


if __name__ == "__main__":
    unittest.main()
