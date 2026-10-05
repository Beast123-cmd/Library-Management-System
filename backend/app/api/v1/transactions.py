import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from app.db.database import get_db
from app.models.models import AuditLog, FinePayment, Transaction, Book, BookCopy, CopyStatus, User, TransactionStatus, HoldQueue, HoldQueueStatus
from app.schemas.schemas import FinePaymentCreate, FineRecordOut, TransactionCreate, TransactionOut, PaginatedResponse, ReturnRequest, ReturnReceipt
from app.core.dependencies import get_current_user, get_current_admin
from app.core.holds import HOLD_DURATION, release_expired_holds
from app.core.copies import available_copy
from app.core.catalog_cache import catalog_cache

router = APIRouter(prefix="/transactions", tags=["Transactions"])

FINE_FIRST_15_DAYS = 5.0    # ₹5/day for first 15 days
FINE_AFTER_15_DAYS = 50.0   # ₹50/day after 15 days
DEFAULT_LOAN_DAYS = 7


def calculate_fine(expected_return: date, actual_return: date) -> float:
    """Business logic: calculate overdue fine based on return dates."""
    if actual_return <= expected_return:
        return 0.0
    overdue_days = (actual_return - expected_return).days
    if overdue_days <= 15:
        return overdue_days * FINE_FIRST_15_DAYS
    return (15 * FINE_FIRST_15_DAYS) + ((overdue_days - 15) * FINE_AFTER_15_DAYS)


from sqlalchemy.orm import selectinload

@router.get("/", response_model=PaginatedResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List transactions. Admins see all; members see their own."""
    query = select(Transaction).options(selectinload(Transaction.user), selectinload(Transaction.book), selectinload(Transaction.copy))
    count_query = select(func.count()).select_from(Transaction)

    if current_user.role.value != "admin":
        member_loan_statuses = [TransactionStatus.issued, TransactionStatus.returned, TransactionStatus.overdue, TransactionStatus.lost]
        query = query.where(Transaction.user_id == current_user.id, Transaction.status.in_(member_loan_statuses))
        count_query = count_query.where(Transaction.user_id == current_user.id, Transaction.status.in_(member_loan_statuses))

    if status_filter:
        query = query.where(Transaction.status == status_filter)
        count_query = count_query.where(Transaction.status == status_filter)

    if search:
        query = query.join(Transaction.book).join(Transaction.user).where(
            (Book.title.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%"))
        )
        count_query = count_query.join(Transaction.book).join(Transaction.user).where(
            (Book.title.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%"))
        )

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * per_page
    result = await db.execute(
        query.offset(offset).limit(per_page).order_by(Transaction.id.desc())
    )
    transactions = result.scalars().all()
    renewal_counts = {}
    if transactions:
        renewal_counts = dict((await db.execute(
            select(AuditLog.resource_id, func.count(AuditLog.id))
            .where(
                AuditLog.action == "loan_renewed",
                AuditLog.resource == "transaction",
                AuditLog.resource_id.in_([txn.id for txn in transactions]),
            )
            .group_by(AuditLog.resource_id)
        )).all())

    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        data=[TransactionOut.model_validate(t).model_copy(update={"renewal_count": renewal_counts.get(t.id, 0)}) for t in transactions]
    )


@router.post("/{txn_id}/renew", response_model=TransactionOut)
async def renew_loan(
    txn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow a member one seven-day renewal before the due date."""
    await release_expired_holds(db)
    await db.flush()
    txn = (await db.execute(
        select(Transaction)
        .where(Transaction.id == txn_id, Transaction.user_id == current_user.id)
        .with_for_update()
    )).scalar_one_or_none()
    if txn is None:
        raise HTTPException(status_code=404, detail="Loan not found.")
    if txn.status != TransactionStatus.issued or txn.expected_return_date < date.today():
        raise HTTPException(status_code=400, detail="Only active, non-overdue loans can be renewed.")

    renewal_count = (await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.action == "loan_renewed",
            AuditLog.resource == "transaction",
            AuditLog.resource_id == txn.id,
        )
    )).scalar_one()
    if renewal_count >= 1:
        raise HTTPException(status_code=400, detail="This loan has already been renewed once.")

    waiting_hold = (await db.execute(
        select(HoldQueue.id).where(
            HoldQueue.book_id == txn.book_id,
            HoldQueue.user_id != current_user.id,
            HoldQueue.status.in_([HoldQueueStatus.active, HoldQueueStatus.suspended]),
        ).limit(1)
    )).scalar_one_or_none()
    if waiting_hold is not None:
        raise HTTPException(status_code=400, detail="Another member has reserved this book.")

    old_due_date = txn.expected_return_date
    txn.expected_return_date += timedelta(days=7)
    db.add(AuditLog(
        action="loan_renewed",
        resource="transaction",
        resource_id=txn.id,
        details=f"member_id={current_user.id}; old_due={old_due_date}; new_due={txn.expected_return_date}",
    ))
    await db.commit()
    catalog_cache.invalidate()
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book), selectinload(Transaction.copy))
        .where(Transaction.id == txn.id)
    )
    return TransactionOut.model_validate(result.scalar_one()).model_copy(update={"renewal_count": 1})


@router.post("/issue", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def issue_book(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Issue a book to a member. Admin only."""
    await release_expired_holds(db)
    await db.flush()
    # Verify book exists
    book_result = await db.execute(select(Book).where(Book.id == payload.book_id).with_for_update())
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    # Verify member exists
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found.")

    # Check if there is an existing on_hold_shelf transaction for this user & book
    hold_txn_result = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == payload.user_id,
            Transaction.book_id == payload.book_id,
            Transaction.status == TransactionStatus.on_hold_shelf
        )
    )
    hold_txn = hold_txn_result.scalar_one_or_none()

    if hold_txn:
        # Convert hold to actual issue
        hold_txn.status = TransactionStatus.issued
        hold_txn.issue_date = date.today()
        hold_txn.expected_return_date = payload.expected_return_date
        txn = hold_txn
        copy = await db.get(BookCopy, hold_txn.copy_id, with_for_update=True) if hold_txn.copy_id else None
        if not copy:
            raise HTTPException(status_code=409, detail="This reserved copy needs an inventory record before it can be issued.")
        copy.status = CopyStatus.issued
        hold_result = await db.execute(
            select(HoldQueue).where(
                HoldQueue.user_id == payload.user_id,
                HoldQueue.book_id == payload.book_id,
                HoldQueue.status.in_([HoldQueueStatus.active, HoldQueueStatus.suspended]),
            )
        )
        hold = hold_result.scalar_one_or_none()
        if hold:
            hold.status = HoldQueueStatus.fulfilled
    else:
        # Standard issue without hold
        if book.available_copies < 1:
            raise HTTPException(status_code=400, detail="No copies of this book are currently available.")
        
        copy = await available_copy(db, book.id)
        if not copy:
            raise HTTPException(status_code=409, detail="Available copies need inventory records before this book can be issued.")
        copy.status = CopyStatus.issued
        txn = Transaction(
            user_id=payload.user_id,
            book_id=payload.book_id,
            copy_id=copy.id,
            issue_date=date.today(),
            expected_return_date=payload.expected_return_date,
            status=TransactionStatus.issued
        )
        book.available_copies -= 1
        db.add(txn)

    await db.commit()
    catalog_cache.invalidate()
    
    # Reload with relationships loaded for serialization
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book), selectinload(Transaction.copy))
        .where(Transaction.id == txn.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/fines", response_model=list[FineRecordOut])
async def list_fines(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Show charged fines and their payment state to staff."""
    rows = (await db.execute(
        select(Transaction, User.name, Book.title, FinePayment)
        .join(User, Transaction.user_id == User.id)
        .join(Book, Transaction.book_id == Book.id)
        .outerjoin(FinePayment, FinePayment.transaction_id == Transaction.id)
        .where(Transaction.status == TransactionStatus.returned, Transaction.fine_amount > 0)
        .order_by(Transaction.actual_return_date.desc(), Transaction.id.desc())
    )).all()
    return [FineRecordOut(
        transaction_id=transaction.id,
        member_name=member_name,
        book_title=book_title,
        assessed_amount=transaction.fine_amount,
        paid_amount=payment.amount if payment else 0.0,
        outstanding_amount=round(transaction.fine_amount - (payment.amount if payment else 0.0), 2),
        paid_at=payment.received_at if payment else None,
        note=payment.note if payment else None,
    ) for transaction, member_name, book_title, payment in rows]


@router.post("/{txn_id}/fine-payment", response_model=FineRecordOut)
async def record_fine_payment(
    txn_id: int,
    payload: FinePaymentCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Record one payment against a returned loan's assessed fine."""
    transaction = (await db.execute(
        select(Transaction)
        .where(Transaction.id == txn_id)
        .with_for_update()
    )).scalar_one_or_none()
    if transaction is None or transaction.status != TransactionStatus.returned or transaction.fine_amount <= 0:
        raise HTTPException(status_code=404, detail="Fine record not found.")
    payment = (await db.execute(
        select(FinePayment).where(FinePayment.transaction_id == txn_id).with_for_update()
    )).scalar_one_or_none()
    paid_amount = payment.amount if payment else 0.0
    outstanding = round(transaction.fine_amount - paid_amount, 2)
    if payload.amount > outstanding:
        raise HTTPException(status_code=400, detail=f"Payment cannot exceed the outstanding ₹{outstanding:.2f}.")
    if payment:
        payment.amount = round(payment.amount + payload.amount, 2)
        payment.note = payload.note or payment.note
    else:
        payment = FinePayment(transaction_id=txn_id, amount=round(payload.amount, 2), note=payload.note, received_by_id=admin.id)
        db.add(payment)
    db.add(AuditLog(
        admin_id=admin.id, action="fine_payment_recorded", resource="transaction", resource_id=txn_id,
        details=json.dumps({"amount": payload.amount, "note": payload.note}),
    ))
    await db.commit()
    await db.refresh(payment)
    member = await db.get(User, transaction.user_id)
    book = await db.get(Book, transaction.book_id)
    return FineRecordOut(
        transaction_id=transaction.id, member_name=member.name, book_title=book.title,
        assessed_amount=transaction.fine_amount, paid_amount=payment.amount,
        outstanding_amount=round(transaction.fine_amount - payment.amount, 2),
        paid_at=payment.received_at, note=payment.note,
    )




@router.get("/{txn_id}/receipt", response_model=ReturnReceipt)
async def get_return_receipt(
    txn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Show a completed return to staff or the member who borrowed it."""
    txn = (await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book), selectinload(Transaction.copy))
        .where(Transaction.id == txn_id)
    )).scalar_one_or_none()
    if txn is None or (current_user.role.value != "admin" and txn.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Return receipt not found.")
    if txn.status != TransactionStatus.returned or txn.actual_return_date is None:
        raise HTTPException(status_code=400, detail="This loan has not been returned.")

    audit = (await db.execute(
        select(AuditLog)
        .where(AuditLog.action == "book_returned", AuditLog.resource == "transaction", AuditLog.resource_id == txn.id)
        .order_by(AuditLog.id.desc())
        .limit(1)
    )).scalar_one_or_none()
    details = json.loads(audit.details) if audit else {}
    return ReturnReceipt.model_validate({
        **TransactionOut.model_validate(txn).model_dump(),
        "overdue_days": max(0, (txn.actual_return_date - txn.expected_return_date).days),
        "assessed_fine": details.get("assessed_fine", txn.fine_amount),
        "waived": details.get("waived", False),
        "waiver_reason": details.get("waiver_reason"),
    })


@router.post("/{txn_id}/return", response_model=ReturnReceipt)
async def return_book(
    txn_id: int,
    payload: ReturnRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Process a book return and calculate any fines. Admin only."""
    await release_expired_holds(db)
    await db.flush()
    txn_result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book))
        .where(Transaction.id == txn_id)
        .with_for_update()
    )
    txn = txn_result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if txn.status not in (TransactionStatus.issued, TransactionStatus.overdue):
        raise HTTPException(status_code=400, detail="Only issued books can be returned.")

    today = date.today()
    assessed_fine = calculate_fine(txn.expected_return_date, today)
    fine = 0.0 if payload.waive_fine else assessed_fine

    txn.actual_return_date = today
    txn.fine_amount = fine
    txn.status = TransactionStatus.returned
    db.add(AuditLog(
        admin_id=admin.id,
        action="book_returned",
        resource="transaction",
        resource_id=txn.id,
        details=json.dumps({
            "assessed_fine": assessed_fine,
            "waived": payload.waive_fine,
            "waiver_reason": payload.waiver_reason,
        }),
    ))

    # Handle book availability and hold trapping
    book_result = await db.execute(select(Book).where(Book.id == txn.book_id).with_for_update())
    book = book_result.scalar_one_or_none()
    
    if book:
        copy = await db.get(BookCopy, txn.copy_id, with_for_update=True) if txn.copy_id else None
        if not copy:
            raise HTTPException(status_code=409, detail="This loan needs an inventory record before it can be returned.")
        # A new hold already has a shelf transaction. Only route a returned copy
        # to an older queued hold that is still waiting for one.
        has_shelf_copy = select(Transaction.id).where(
            Transaction.user_id == HoldQueue.user_id,
            Transaction.book_id == HoldQueue.book_id,
            Transaction.status == TransactionStatus.on_hold_shelf,
        ).exists()
        hold_result = await db.execute(
            select(HoldQueue)
            .where(HoldQueue.book_id == book.id)
            .where(HoldQueue.status == HoldQueueStatus.active)
            .where(~has_shelf_copy)
            .order_by(HoldQueue.request_date.asc())
            .limit(1)
        )
        next_hold = hold_result.scalar_one_or_none()
        
        if next_hold:
            # Reserve the returned copy for the same 12-hour pickup window.
            next_hold.expiration_date = datetime.now(timezone.utc) + HOLD_DURATION
            new_txn = Transaction(
                book_id=book.id,
                user_id=next_hold.user_id,
                copy_id=copy.id,
                status=TransactionStatus.on_hold_shelf,
                issue_date=today,
                expected_return_date=next_hold.expiration_date.date(),
            )
            db.add(new_txn)
            copy.status = CopyStatus.on_hold_shelf
        else:
            book.available_copies += 1
            copy.status = CopyStatus.available

    await db.commit()
    catalog_cache.invalidate()
    return await get_return_receipt(txn.id, db, admin)
