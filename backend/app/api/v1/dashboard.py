from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.models.models import Book, User, Transaction, TransactionStatus, UserRole
from app.core.dependencies import get_current_user
from app.schemas.schemas import TransactionOut, BookOut
from typing import Dict, Any, List

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve statistics for the main dashboard dashboard."""
    # 1. Total Books Count
    total_books = (await db.execute(select(func.count()).select_from(Book))).scalar() or 0

    # 2. Total Members Count
    total_members = (await db.execute(
        select(func.count()).select_from(User).where(User.role == UserRole.member)
    )).scalar() or 0

    # 3. Active Loans Count
    active_loans = (await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.status == TransactionStatus.issued)
    )).scalar() or 0

    # 4. Total Fines (Sum of fine_amount)
    total_fines = (await db.execute(
        select(func.sum(Transaction.fine_amount))
    )).scalar() or 0.0

    # 5. Low Stock Alert Books (available_copies < 2)
    low_stock_result = await db.execute(
        select(Book).where(Book.available_copies < 2).order_by(Book.available_copies.asc()).limit(10)
    )
    low_stock_books = low_stock_result.scalars().all()

    # 6. Recent Activity Feed (latest 8 transactions)
    recent_txns_result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book))
        .order_by(desc(Transaction.id))
        .limit(8)
    )
    recent_txns = recent_txns_result.scalars().all()

    # 7. Member Activity Rankings (most active readers)
    rankings_result = await db.execute(
        select(User.name, User.username, func.count(Transaction.id).label("txn_count"))
        .join(Transaction, User.id == Transaction.user_id)
        .where(User.role == UserRole.member)
        .group_by(User.id, User.name, User.username)
        .order_by(desc("txn_count"))
        .limit(5)
    )
    member_rankings = [{"name": r[0], "username": r[1], "count": r[2]} for r in rankings_result.all()]

    # 8. Current Books Issued to Members (holding the most library property)
    holding_result = await db.execute(
        select(User.name, User.username, func.count(Transaction.id).label("active_count"))
        .join(Transaction, User.id == Transaction.user_id)
        .where(User.role == UserRole.member, Transaction.status == TransactionStatus.issued)
        .group_by(User.id, User.name, User.username)
        .order_by(desc("active_count"))
        .limit(5)
    )
    active_loans_by_member = [{"name": r[0], "username": r[1], "count": r[2]} for r in holding_result.all()]

    # Convert to appropriate schemas/dicts
    return {
        "kpis": {
            "total_books": total_books,
            "total_members": total_members,
            "active_loans": active_loans,
            "total_fines": float(total_fines)
        },
        "low_stock_books": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "available_copies": b.available_copies,
                "total_copies": b.total_copies
            } for b in low_stock_books
        ],
        "recent_activity": [
            {
                "id": t.id,
                "user_name": t.user.name if t.user else "Unknown Member",
                "book_title": t.book.title if t.book else "Unknown Book",
                "action": "issued" if t.status == TransactionStatus.issued else "returned",
                "date": str(t.actual_return_date or t.issue_date)
            } for t in recent_txns
        ],
        "member_rankings": member_rankings,
        "active_loans_by_member": active_loans_by_member
    }
