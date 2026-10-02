from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Book, BookCopy, CopyStatus, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus

HOLD_DURATION = timedelta(hours=12)


async def release_expired_holds(db: AsyncSession) -> None:
    """Release copies reserved by holds whose pickup window has elapsed."""
    expired_holds = (
        await db.execute(
            select(HoldQueue)
            .where(
                HoldQueue.status.in_([HoldQueueStatus.active, HoldQueueStatus.suspended]),
                HoldQueue.expiration_date < datetime.now(timezone.utc),
            )
            .with_for_update(skip_locked=True)
        )
    ).scalars().all()

    for hold in expired_holds:
        hold.status = HoldQueueStatus.expired
        book = await db.get(Book, hold.book_id)
        if book:
            book.available_copies += 1
        hold_transaction = (
            await db.execute(
                select(Transaction).where(
                    Transaction.user_id == hold.user_id,
                    Transaction.book_id == hold.book_id,
                    Transaction.status == TransactionStatus.on_hold_shelf,
                )
            )
        ).scalar_one_or_none()
        if hold_transaction:
            copy = await db.get(BookCopy, hold_transaction.copy_id, with_for_update=True) if hold_transaction.copy_id else None
            if copy:
                copy.status = CopyStatus.available
            await db.delete(hold_transaction)
