from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from app.db.database import get_db
from app.models.models import Book
from app.schemas.schemas import BookCreate, BookUpdate, BookOut, PaginatedResponse
from app.core.dependencies import get_current_user, get_current_admin
from app.models.models import User

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=PaginatedResponse)
async def list_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """List all books with pagination and optional search."""
    query = select(Book)
    count_query = select(func.count()).select_from(Book)

    if search:
        filter_expr = or_(
            Book.title.ilike(f"%{search}%"),
            Book.author.ilike(f"%{search}%"),
            Book.isbn.ilike(f"%{search}%")
        )
        query = query.where(filter_expr)
        count_query = count_query.where(filter_expr)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page).order_by(Book.title))
    books = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        per_page=per_page,
        data=[BookOut.model_validate(b) for b in books]
    )


@router.get("/{book_id}", response_model=BookOut)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Get a single book by ID."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book


@router.post("/", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Create a new book. Admin only."""
    if payload.isbn:
        existing = await db.execute(select(Book).where(Book.isbn == payload.isbn))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="A book with this ISBN already exists.")

    book = Book(
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        publish_year=payload.publish_year,
        total_copies=payload.total_copies,
        available_copies=payload.total_copies,
        cover_url=payload.cover_url
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@router.patch("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Update book details. Admin only."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if "total_copies" in update_data:
        diff = update_data["total_copies"] - book.total_copies
        if book.available_copies + diff < 0:
            raise HTTPException(status_code=400, detail="Cannot reduce total copies below currently checked out copies.")
        book.available_copies += diff

    for field, value in update_data.items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Delete a book. Admin only."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    await db.delete(book)
    await db.commit()
