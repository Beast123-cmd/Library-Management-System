from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import HoldQueue, HoldQueueStatus, Transaction, TransactionStatus, User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Build the current user's actionable library alerts from live records."""
    if user.role.value == "admin":
        return []
    today = date.today()
    alerts = []
    loans = (await db.execute(
        select(Transaction).options(selectinload(Transaction.book)).where(
            Transaction.user_id == user.id, Transaction.status == TransactionStatus.issued,
        )
    )).scalars().all()
    for loan in loans:
        title = loan.book.title if loan.book else "A library book"
        if user.notify_overdue and loan.expected_return_date < today:
            alerts.append({"id": f"overdue-{loan.id}", "type": "overdue", "title": "Book overdue", "message": f"{title} was due {loan.expected_return_date}.", "action": "/dashboard/transactions", "created_at": str(loan.expected_return_date)})
        elif user.notify_due and loan.expected_return_date <= today + timedelta(days=2):
            alerts.append({"id": f"due-{loan.id}", "type": "due", "title": "Due soon", "message": f"{title} is due {loan.expected_return_date}.", "action": "/dashboard/transactions", "created_at": str(loan.expected_return_date)})
    if user.notify_holds:
        holds = (await db.execute(
            select(HoldQueue).options(selectinload(HoldQueue.book)).where(
                HoldQueue.user_id == user.id, HoldQueue.status == HoldQueueStatus.active,
            )
        )).scalars().all()
        for hold in holds:
            title = hold.book.title if hold.book else "Your reserved book"
            alerts.append({"id": f"hold-{hold.id}", "type": "hold", "title": "Ready for pickup", "message": f"{title} is ready to collect before {hold.expiration_date.astimezone(timezone.utc).strftime('%d %b, %H:%M UTC') if hold.expiration_date else 'its pickup deadline'}.", "action": "/dashboard", "created_at": hold.expiration_date.isoformat() if hold.expiration_date else datetime.now(timezone.utc).isoformat()})
    return sorted(alerts, key=lambda alert: alert["created_at"])
