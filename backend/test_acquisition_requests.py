import unittest

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.acquisitions import create_request, list_requests, review_request
from app.db.database import Base
from app.models.models import User, UserRole
from app.schemas.schemas import AcquisitionRequestCreate, AcquisitionRequestReview


class AcquisitionRequestTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_member_request_can_be_approved_by_staff(self):
        async with self.sessions() as db:
            admin = User(name="Admin", email="admin@example.com", username="admin", hashed_password="x", role=UserRole.admin)
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            db.add_all([admin, member]); await db.commit()
            created = await create_request(AcquisitionRequestCreate(title="Requested book", author="Author"), db, member)
            self.assertEqual(len(await list_requests(db, member)), 1)
            reviewed = await review_request(created["id"], AcquisitionRequestReview(status="approved", staff_note="Ordered"), db, admin)
            self.assertEqual(reviewed["status"], "approved")
            self.assertEqual(reviewed["staff_note"], "Ordered")


if __name__ == "__main__":
    unittest.main()
