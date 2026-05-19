from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import Optional
from app.db.database import get_db
from app.models.models import Transaction, Book, User, TransactionStatus
from app.schemas.schemas import TransactionCreate, TransactionOut, PaginatedResponse, ReturnRequest
from app.core.dependencies import get_current_user, get_current_admin

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
    query = select(Transaction).options(selectinload(Transaction.user), selectinload(Transaction.book))
    count_query = select(func.count()).select_from(Transaction)

    if current_user.role.value != "admin":
        query = query.where(Transaction.user_id == current_user.id)
        count_query = count_query.where(Transaction.user_id == current_user.id)

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
    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        data=[TransactionOut.model_validate(t) for t in transactions]
    )


@router.post("/issue", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def issue_book(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Issue a book to a member. Admin only."""
    # Verify book exists and has available copies
    book_result = await db.execute(select(Book).where(Book.id == payload.book_id))
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No copies of this book are currently available.")

    # Verify member exists
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found.")

    txn = Transaction(
        user_id=payload.user_id,
        book_id=payload.book_id,
        issue_date=date.today(),
        expected_return_date=payload.expected_return_date,
        status=TransactionStatus.issued
    )
    book.available_copies -= 1

    db.add(txn)
    await db.commit()
    
    # Reload with relationships loaded for serialization
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book))
        .where(Transaction.id == txn.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/borrow/{book_id}", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def borrow_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Borrow a book for the current logged-in user."""
    # Verify book exists and has available copies
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No copies of this book are currently available.")

    # Check if user already has an active issue for this book
    active_txn = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.book_id == book_id,
            Transaction.status == TransactionStatus.issued
        )
    )
    if active_txn.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already borrowed this book.")

    txn = Transaction(
        user_id=current_user.id,
        book_id=book_id,
        issue_date=date.today(),
        expected_return_date=date.today() + timedelta(days=DEFAULT_LOAN_DAYS),
        status=TransactionStatus.issued
    )
    book.available_copies -= 1

    db.add(txn)
    await db.commit()
    
    # Reload with relationships loaded for serialization
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book))
        .where(Transaction.id == txn.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()



@router.post("/{txn_id}/return", response_model=TransactionOut)
async def return_book(
    txn_id: int,
    payload: ReturnRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Process a book return and calculate any fines. Admin only."""
    txn_result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.book))
        .where(Transaction.id == txn_id)
    )
    txn = txn_result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if txn.status == TransactionStatus.returned:
        raise HTTPException(status_code=400, detail="This book has already been returned.")

    today = date.today()
    fine = 0.0 if payload.waive_fine else calculate_fine(txn.expected_return_date, today)

    txn.actual_return_date = today
    txn.fine_amount = fine
    txn.status = TransactionStatus.returned

    # Restore book availability
    book_result = await db.execute(select(Book).where(Book.id == txn.book_id))
    book = book_result.scalar_one_or_none()
    if book:
        book.available_copies += 1

    await db.commit()
    await db.refresh(txn)
    return txn
