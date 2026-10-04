import unittest

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.users import get_notification_preferences, update_notification_preferences
from app.db.database import Base
from app.models.models import User
from app.schemas.schemas import NotificationPreferencesUpdate


class NotificationPreferenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_member_can_save_individual_alert_preferences(self):
        async with self.sessions() as db:
            member = User(name="Member", email="member@example.com", username="member", hashed_password="x")
            db.add(member)
            await db.commit()

            defaults = await get_notification_preferences(member)
            self.assertTrue(defaults.due_reminders)
            saved = await update_notification_preferences(
                NotificationPreferencesUpdate(overdue_alerts=False), db, member
            )
            self.assertTrue(saved.due_reminders)
            self.assertFalse(saved.overdue_alerts)
            self.assertTrue(saved.hold_ready_alerts)


if __name__ == "__main__":
    unittest.main()
