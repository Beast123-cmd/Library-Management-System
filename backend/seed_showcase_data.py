"""Safely add professional demo content without deleting existing library data.

Run from backend: venv/bin/python seed_showcase_data.py
The audit marker makes this script idempotent.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.copies import add_copies
from app.core.security import get_password_hash
from app.db.database import AsyncSessionLocal, engine
from app.models.models import (
    AuditLog,
    Book,
    BookCopy,
    CopyStatus,
    HoldQueue,
    HoldQueueStatus,
    Transaction,
    TransactionStatus,
    User,
    UserRole,
)


BOOKS = [
    ("The Midnight Library", "Matt Haig", "9780525559474", 2020, "Contemporary Fiction", "English", "Viking", "A-01", 4),
    ("Project Hail Mary", "Andy Weir", "9780593135204", 2021, "Science Fiction", "English", "Ballantine Books", "A-04", 5),
    ("Klara and the Sun", "Kazuo Ishiguro", "9780593318171", 2021, "Literary Fiction", "English", "Knopf", "A-07", 3),
    ("The Psychology of Money", "Morgan Housel", "9780857197689", 2020, "Personal Finance", "English", "Harriman House", "B-03", 4),
    ("Deep Work", "Cal Newport", "9781455586691", 2016, "Productivity", "English", "Grand Central", "B-08", 4),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "9781449373320", 2017, "Technology", "English", "O'Reilly Media", "C-02", 3),
    ("The Design of Everyday Things", "Don Norman", "9780465050659", 2013, "Design", "English", "Basic Books", "C-05", 3),
    ("Sapiens", "Yuval Noah Harari", "9780062316097", 2015, "History", "English", "Harper", "D-01", 5),
    ("A Brief History of Time", "Stephen Hawking", "9780553380163", 1998, "Science", "English", "Bantam", "D-06", 3),
    ("Ikigai", "Héctor García", "9780143130727", 2017, "Wellbeing", "English", "Penguin", "E-02", 4),
    ("The Song of Achilles", "Madeline Miller", "9780062060624", 2012, "Historical Fiction", "English", "Ecco", "E-06", 3),
    ("Educated", "Tara Westover", "9780399590504", 2018, "Memoir", "English", "Random House", "F-01", 3),
]

MEMBERS = [
    ("Ananya Rao", "ananya.rao@demo.library", "ananya_rao"),
    ("Kabir Mehta", "kabir.mehta@demo.library", "kabir_mehta"),
    ("Meera Shah", "meera.shah@demo.library", "meera_shah"),
    ("Arjun Kapoor", "arjun.kapoor@demo.library", "arjun_kapoor"),
]


async def first_available_copy(db, book_id: int) -> BookCopy:
    result = await db.execute(
        select(BookCopy)
        .where(BookCopy.book_id == book_id, BookCopy.status == CopyStatus.available)
        .order_by(BookCopy.copy_number)
    )
    return result.scalars().first()


async def main():
    async with AsyncSessionLocal() as db:
        existing_marker = await db.execute(select(AuditLog.id).where(AuditLog.action == "showcase_data_seeded"))
        if existing_marker.scalar_one_or_none():
            print("Showcase data already exists; no changes made.")
            return

        books_by_isbn: dict[str, Book] = {}
        for title, author, isbn, year, category, language, publisher, shelf, copies in BOOKS:
            book = (await db.execute(select(Book).where(Book.isbn == isbn))).scalar_one_or_none()
            if not book:
                book = Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    publish_year=year,
                    category=category,
                    language=language,
                    publisher=publisher,
                    shelf_location=shelf,
                    total_copies=copies,
                    available_copies=copies,
                    cover_url=f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
                    description=f"A curated library edition of {title} by {author}.",
                )
                db.add(book)
                await db.flush()
                await add_copies(db, book, copies)
            books_by_isbn[isbn] = book

        members: list[User] = []
        password_hash = get_password_hash("Library2026!")
        for name, email, username in MEMBERS:
            member = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
            if not member:
                member = User(name=name, email=email, username=username, hashed_password=password_hash, role=UserRole.member)
                db.add(member)
                await db.flush()
            members.append(member)

        today = date.today()
        books = list(books_by_isbn.values())
        # Returned loans supply a realistic activity/history baseline without affecting stock.
        for index in range(12):
            book = books[index % len(books)]
            copy = await first_available_copy(db, book.id)
            issued = today - timedelta(days=75 - index * 4)
            returned = issued + timedelta(days=8 + index % 4)
            db.add(Transaction(
                user_id=members[index % len(members)].id,
                book_id=book.id,
                copy_id=copy.id if copy else None,
                issue_date=issued,
                expected_return_date=issued + timedelta(days=14),
                actual_return_date=returned,
                status=TransactionStatus.returned,
                fine_amount=0.0,
            ))

        # Three live circulation states populate staff work queues and member views.
        due_book, overdue_book, hold_book = books[:3]
        for member, book, due_date in (
            (members[0], due_book, today),
            (members[1], overdue_book, today - timedelta(days=4)),
        ):
            copy = await first_available_copy(db, book.id)
            if copy:
                copy.status = CopyStatus.issued
                book.available_copies -= 1
                db.add(Transaction(
                    user_id=member.id,
                    book_id=book.id,
                    copy_id=copy.id,
                    issue_date=today - timedelta(days=7),
                    expected_return_date=due_date,
                    status=TransactionStatus.issued,
                    fine_amount=0.0,
                ))

        hold_copy = await first_available_copy(db, hold_book.id)
        if hold_copy:
            hold_copy.status = CopyStatus.on_hold_shelf
            hold_book.available_copies -= 1
            hold = HoldQueue(
                user_id=members[2].id,
                book_id=hold_book.id,
                status=HoldQueueStatus.active,
                expiration_date=datetime.now(timezone.utc) + timedelta(hours=6),
            )
            db.add(hold)
            await db.flush()
            db.add(Transaction(
                user_id=members[2].id,
                book_id=hold_book.id,
                copy_id=hold_copy.id,
                issue_date=today,
                expected_return_date=today + timedelta(days=7),
                status=TransactionStatus.on_hold_shelf,
            ))

        admin = (await db.execute(select(User).where(User.role == UserRole.admin).order_by(User.id))).scalars().first()
        db.add_all([
            AuditLog(admin_id=admin.id if admin else None, action="book_returned", resource="transaction", details="Showcase return history created"),
            AuditLog(admin_id=admin.id if admin else None, action="catalog_updated", resource="book", details="Showcase catalogue created"),
            AuditLog(admin_id=admin.id if admin else None, action="showcase_data_seeded", resource="system", details="Safe professional demo data seed"),
        ])
        await db.commit()
        print(f"Added {len(BOOKS)} curated titles, {len(MEMBERS)} members, and circulation activity.")
        print("Demo members use password: Library2026!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
