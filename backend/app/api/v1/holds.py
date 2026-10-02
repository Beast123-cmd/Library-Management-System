from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, date, timezone

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.core.holds import HOLD_DURATION, release_expired_holds
from app.models.models import User, Book, BookCopy, CopyStatus, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus
from app.schemas.schemas import HoldQueueOut
from app.core.copies import available_copy

router = APIRouter(prefix="/holds", tags=["Holds"])

@router.get("/all", response_model=List[HoldQueueOut])
async def get_all_holds(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Get all holds across the system (Admin only) - Pull List."""
    await release_expired_holds(db)
    await db.commit()
    stmt = (
        select(HoldQueue)
        .options(selectinload(HoldQueue.book), selectinload(HoldQueue.user))
        .where(
            HoldQueue.status.in_([HoldQueueStatus.active, HoldQueueStatus.suspended])
        )
        .order_by(HoldQueue.request_date.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{book_id}", response_model=HoldQueueOut, status_code=status.HTTP_201_CREATED)
async def place_hold(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reserve one available copy for collection within 12 hours."""
    await release_expired_holds(db)
    await db.flush()
    # Serialize reservations by this member, including holds on different books.
    await db.execute(select(User.id).where(User.id == current_user.id).with_for_update())
    existing_hold_result = await db.execute(
        select(HoldQueue).where(
            HoldQueue.user_id == current_user.id,
            HoldQueue.status.in_([HoldQueueStatus.active, HoldQueueStatus.suspended]),
        ).limit(1)
    )
    if existing_hold_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You can hold only one book at a time. Collect or cancel your current hold first.")

    book_result = await db.execute(select(Book).where(Book.id == book_id).with_for_update())
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No copies are currently available to hold.")

    copy = await available_copy(db, book.id)
    if not copy:
        raise HTTPException(status_code=409, detail="Available copies need inventory records before this book can be held.")

    expires_at = datetime.now(timezone.utc) + HOLD_DURATION
    new_hold = HoldQueue(
        user_id=current_user.id,
        book_id=book_id,
        expiration_date=expires_at,
        status=HoldQueueStatus.active,
    )
    db.add(new_hold)
    db.add(Transaction(
        user_id=current_user.id,
        book_id=book_id,
        copy_id=copy.id,
        issue_date=date.today(),
        expected_return_date=expires_at.date(),
        status=TransactionStatus.on_hold_shelf,
    ))
    copy.status = CopyStatus.on_hold_shelf
    book.available_copies -= 1
    await db.commit()
    await db.refresh(new_hold)

    stmt = select(HoldQueue).options(selectinload(HoldQueue.book)).where(HoldQueue.id == new_hold.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.get("/my-holds", response_model=List[HoldQueueOut])
async def get_my_holds(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active holds for the current user."""
    await release_expired_holds(db)
    await db.commit()
    stmt = (
        select(HoldQueue)
        .options(selectinload(HoldQueue.book))
        .where(
            HoldQueue.user_id == current_user.id,
            HoldQueue.status.in_([HoldQueueStatus.active, HoldQueueStatus.suspended])
        )
        .order_by(HoldQueue.request_date.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{hold_id}/suspend", response_model=HoldQueueOut)
async def suspend_hold(
    hold_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suspend an active hold."""
    await release_expired_holds(db)
    result = await db.execute(select(HoldQueue).where(HoldQueue.id == hold_id, HoldQueue.user_id == current_user.id))
    hold = result.scalar_one_or_none()
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found.")
    
    if hold.status != HoldQueueStatus.active:
        raise HTTPException(status_code=400, detail="Only active holds can be suspended.")
        
    hold.status = HoldQueueStatus.suspended
    await db.commit()
    
    stmt = select(HoldQueue).options(selectinload(HoldQueue.book)).where(HoldQueue.id == hold_id)
    ret = await db.execute(stmt)
    return ret.scalar_one()

@router.post("/{hold_id}/activate", response_model=HoldQueueOut)
async def activate_hold(
    hold_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reactivate a suspended hold."""
    await release_expired_holds(db)
    result = await db.execute(select(HoldQueue).where(HoldQueue.id == hold_id, HoldQueue.user_id == current_user.id))
    hold = result.scalar_one_or_none()
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found.")
    
    if hold.status != HoldQueueStatus.suspended:
        raise HTTPException(status_code=400, detail="Only suspended holds can be reactivated.")
        
    hold.status = HoldQueueStatus.active
    await db.commit()
    
    stmt = select(HoldQueue).options(selectinload(HoldQueue.book)).where(HoldQueue.id == hold_id)
    ret = await db.execute(stmt)
    return ret.scalar_one()

@router.post("/{hold_id}/cancel", response_model=HoldQueueOut)
async def cancel_hold(
    hold_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a hold."""
    await release_expired_holds(db)
    result = await db.execute(select(HoldQueue).where(HoldQueue.id == hold_id, HoldQueue.user_id == current_user.id))
    hold = result.scalar_one_or_none()
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found.")
    
    if hold.status not in [HoldQueueStatus.active, HoldQueueStatus.suspended]:
        raise HTTPException(status_code=400, detail="This hold can no longer be cancelled.")

    hold.status = HoldQueueStatus.cancelled
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
    await db.commit()
    
    stmt = select(HoldQueue).options(selectinload(HoldQueue.book)).where(HoldQueue.id == hold_id)
    ret = await db.execute(stmt)
    return ret.scalar_one()
