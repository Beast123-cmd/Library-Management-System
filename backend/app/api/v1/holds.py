from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta, date

from app.db.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.models import User, Book, HoldQueue, HoldQueueStatus, Transaction, TransactionStatus
from app.schemas.schemas import HoldQueueOut

router = APIRouter(prefix="/holds", tags=["Holds"])

@router.get("/all", response_model=List[HoldQueueOut])
async def get_all_holds(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user)
):
    """Get all holds across the system (Admin only) - Pull List."""
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
    """Place a hold on a book."""
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    # Check if they already have an active hold
    existing_hold_result = await db.execute(
        select(HoldQueue).where(
            HoldQueue.user_id == current_user.id,
            HoldQueue.book_id == book_id,
            HoldQueue.status == HoldQueueStatus.active
        )
    )
    if existing_hold_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have an active hold on this book.")

    # If copies are available, book directly goes to on_hold_shelf (trapped for this user)
    # If not, it joins the waitlist.
    if book.available_copies > 0:
        # We can issue it immediately to the hold shelf
        txn = Transaction(
            user_id=current_user.id,
            book_id=book_id,
            issue_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7), # hold expires in 7 days
            status=TransactionStatus.on_hold_shelf
        )
        book.available_copies -= 1
        db.add(txn)
        await db.commit()
        # Create a fulfilled hold record for history tracking
        new_hold = HoldQueue(
            user_id=current_user.id,
            book_id=book_id,
            status=HoldQueueStatus.fulfilled
        )
        db.add(new_hold)
        await db.commit()
        await db.refresh(new_hold)
    else:
        new_hold = HoldQueue(
            user_id=current_user.id,
            book_id=book_id,
            status=HoldQueueStatus.active
        )
        db.add(new_hold)
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
    result = await db.execute(select(HoldQueue).where(HoldQueue.id == hold_id, HoldQueue.user_id == current_user.id))
    hold = result.scalar_one_or_none()
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found.")
    
    hold.status = HoldQueueStatus.cancelled
    await db.commit()
    
    stmt = select(HoldQueue).options(selectinload(HoldQueue.book)).where(HoldQueue.id == hold_id)
    ret = await db.execute(stmt)
    return ret.scalar_one()
