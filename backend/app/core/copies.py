from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Book, BookCopy, CopyStatus


def accession_number(book_id: int, copy_number: int) -> str:
    return f"B{book_id}-{copy_number:04d}"


async def add_copies(db: AsyncSession, book: Book, count: int) -> None:
    if count <= 0:
        return
    last_number = (await db.execute(
        select(func.max(BookCopy.copy_number)).where(BookCopy.book_id == book.id)
    )).scalar_one() or 0
    db.add_all([
        BookCopy(
            book_id=book.id,
            copy_number=number,
            accession_number=accession_number(book.id, number),
        )
        for number in range(last_number + 1, last_number + count + 1)
    ])


async def available_copy(db: AsyncSession, book_id: int) -> BookCopy | None:
    return (await db.execute(
        select(BookCopy)
        .where(BookCopy.book_id == book_id, BookCopy.status == CopyStatus.available)
        .order_by(BookCopy.copy_number)
        .with_for_update()
        .limit(1)
    )).scalar_one_or_none()
