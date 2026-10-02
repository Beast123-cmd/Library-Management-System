import unittest

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.books import list_books
from app.db.database import Base
from app.models.models import Book, User


class BookInventoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_filters_return_catalog_metadata(self):
        async with self.sessions() as db:
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            db.add_all([
                member,
                Book(title="Available", author="Author", category="Fiction", language="English", publisher="Press", edition="2nd", shelf_location="A-03", total_copies=1, available_copies=1),
                Book(title="Checked out", author="Author", category="Fiction", language="Hindi", total_copies=1, available_copies=0),
            ])
            await db.commit()

            result = await list_books(1, 20, None, "fiction", "english", True, db, member)

            self.assertEqual(result.total, 1)
            self.assertEqual(result.data[0].publisher, "Press")
            self.assertEqual(result.data[0].shelf_location, "A-03")


if __name__ == "__main__":
    unittest.main()
