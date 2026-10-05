import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, status, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import asc, desc, select, func, or_
from typing import Optional
from app.db.database import get_db
from app.models.models import AuditLog, Book, BookCopy, CopyStatus
from app.schemas.schemas import BookCreate, BookUpdate, BookOut, BookCopyOut, CopyStatusUpdate, PaginatedResponse
from app.core.dependencies import get_current_user, get_current_admin
from app.models.models import User
from app.core.copies import add_copies
from app.core.catalog_cache import catalog_cache
from app.core.config import settings

router = APIRouter(prefix="/books", tags=["Books"])

CSV_FIELDS = ("title", "author", "isbn", "publish_year", "category", "language", "publisher", "edition", "shelf_location", "total_copies", "cover_url", "description")


@router.get("/", response_model=PaginatedResponse)
async def list_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None, max_length=100),
    language: Optional[str] = Query(None, max_length=100),
    author: Optional[str] = Query(None, max_length=150),
    publisher: Optional[str] = Query(None, max_length=150),
    shelf_location: Optional[str] = Query(None, max_length=100),
    available_only: bool = Query(False),
    sort_by: str = Query("title", pattern="^(title|newest|year_desc|year_asc|availability)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    response: Response = None,
):
    """List the catalogue with cached, paginated search results."""
    cache_key = (id(db.bind), page, per_page, search, category, language, author, publisher, shelf_location, available_only, sort_by)
    cached = catalog_cache.get(cache_key)
    if cached is not None:
        if response:
            response.headers["Cache-Control"] = "private, max-age=30"
            response.headers["Vary"] = "Authorization"
        return PaginatedResponse.model_validate(cached)

    query = select(Book)
    count_query = select(func.count()).select_from(Book)

    if search:
        filter_expr = or_(
            Book.title.ilike(f"%{search}%"),
            Book.author.ilike(f"%{search}%"),
            Book.isbn.ilike(f"%{search}%"),
            Book.publisher.ilike(f"%{search}%")
        )
        query = query.where(filter_expr)
        count_query = count_query.where(filter_expr)

    for field, value in (
        (Book.category, category),
        (Book.language, language),
        (Book.author, author),
        (Book.publisher, publisher),
        (Book.shelf_location, shelf_location),
    ):
        if value:
            filter_expr = field.ilike(f"%{value}%")
            query = query.where(filter_expr)
            count_query = count_query.where(filter_expr)

    if available_only:
        query = query.where(Book.available_copies > 0)
        count_query = count_query.where(Book.available_copies > 0)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * per_page
    ordering = {
        "title": asc(Book.title),
        "newest": desc(Book.id),
        "year_desc": desc(Book.publish_year).nullslast(),
        "year_asc": asc(Book.publish_year).nullslast(),
        "availability": desc(Book.available_copies),
    }[sort_by]
    result = await db.execute(query.offset(offset).limit(per_page).order_by(ordering, Book.title))
    books = result.scalars().all()

    payload = PaginatedResponse(
        total=total,
        page=page,
        per_page=per_page,
        data=[BookOut.model_validate(b) for b in books]
    )
    catalog_cache.set(cache_key, payload.model_dump(mode="json"), ttl_seconds=settings.CATALOG_CACHE_TTL_SECONDS)
    if response:
        response.headers["Cache-Control"] = "private, max-age=30"
        response.headers["Vary"] = "Authorization"
    return payload


@router.get("/filter-options")
async def catalog_filter_options(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return curated filter choices once instead of sending users free-text fields."""
    cache_key = (id(db.bind), "filter-options")
    cached = catalog_cache.get(cache_key)
    if cached is not None:
        return cached

    fields = {
        "categories": Book.category,
        "languages": Book.language,
        "authors": Book.author,
        "publishers": Book.publisher,
        "shelves": Book.shelf_location,
    }
    options = {}
    for key, field in fields.items():
        options[key] = list((await db.execute(
            select(field).where(field.is_not(None)).distinct().order_by(field)
        )).scalars())
    catalog_cache.set(cache_key, options, ttl_seconds=300)
    return options


@router.get("/export")
async def export_catalogue(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Export the catalogue in the same format accepted by the importer."""
    books = (await db.execute(select(Book).order_by(Book.title))).scalars().all()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for book in books:
        writer.writerow({field: getattr(book, field) or "" for field in CSV_FIELDS})
    filename = "library-catalogue.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_catalogue(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Create new books and tracked copies from a UTF-8 CSV; existing ISBNs are skipped."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file.")
    try:
        raw = (await file.read()).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="The CSV must use UTF-8 encoding.") from exc

    rows = list(csv.DictReader(io.StringIO(raw)))
    if not rows:
        raise HTTPException(status_code=400, detail="The CSV has no book rows.")
    if not {"title", "author"}.issubset(rows[0].keys()):
        raise HTTPException(status_code=400, detail="CSV requires title and author columns.")
    if len(rows) > 1000:
        raise HTTPException(status_code=400, detail="Import up to 1,000 books at a time.")

    existing_isbns = set((await db.execute(select(Book.isbn).where(Book.isbn.is_not(None)))).scalars())
    created, skipped, errors = 0, 0, []
    for line_number, row in enumerate(rows, start=2):
        title, author = (row.get("title") or "").strip(), (row.get("author") or "").strip()
        isbn = (row.get("isbn") or "").strip() or None
        if not title or not author:
            errors.append(f"Row {line_number}: title and author are required.")
            continue
        if isbn and isbn in existing_isbns:
            skipped += 1
            continue
        try:
            copies = max(1, int((row.get("total_copies") or "1").strip()))
            publish_year = int(row["publish_year"]) if (row.get("publish_year") or "").strip() else None
            if publish_year and not 1000 <= publish_year <= 2100:
                raise ValueError("publish_year must be between 1000 and 2100")
        except ValueError as exc:
            errors.append(f"Row {line_number}: {exc}.")
            continue
        book = Book(
            title=title, author=author, isbn=isbn, publish_year=publish_year,
            category=(row.get("category") or "").strip() or None,
            language=(row.get("language") or "").strip() or None,
            publisher=(row.get("publisher") or "").strip() or None,
            edition=(row.get("edition") or "").strip() or None,
            shelf_location=(row.get("shelf_location") or "").strip() or None,
            total_copies=copies, available_copies=copies,
            cover_url=(row.get("cover_url") or "").strip() or None,
            description=(row.get("description") or "").strip() or None,
        )
        db.add(book)
        await db.flush()
        await add_copies(db, book, copies)
        if isbn:
            existing_isbns.add(isbn)
        created += 1

    await db.commit()
    catalog_cache.invalidate()
    return {"created": created, "skipped": skipped, "errors": errors[:20]}


@router.get("/copies/audit")
async def list_copy_audit(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List physical copies with their current audit-ready status."""
    rows = (await db.execute(
        select(BookCopy, Book.title, Book.author, Book.shelf_location)
        .join(Book, BookCopy.book_id == Book.id)
        .order_by(Book.title, BookCopy.copy_number)
    )).all()
    return [{
        "id": copy.id, "book_id": copy.book_id, "title": title, "author": author,
        "shelf_location": shelf_location, "accession_number": copy.accession_number,
        "copy_number": copy.copy_number, "status": copy.status.value,
    } for copy, title, author, shelf_location in rows]


@router.patch("/copies/{copy_id}/status")
async def update_copy_status(
    copy_id: int,
    payload: CopyStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Record a physical inventory finding without changing active circulation records."""
    copy = (await db.execute(select(BookCopy).where(BookCopy.id == copy_id).with_for_update())).scalar_one_or_none()
    if copy is None:
        raise HTTPException(status_code=404, detail="Copy not found.")
    if copy.status in (CopyStatus.issued, CopyStatus.on_hold_shelf):
        raise HTTPException(status_code=400, detail="Check in this copy before changing its inventory status.")
    previous_status = copy.status.value
    copy.status = CopyStatus(payload.status)
    book = await db.get(Book, copy.book_id, with_for_update=True)
    if book:
        book.available_copies = (await db.execute(
            select(func.count()).select_from(BookCopy).where(BookCopy.book_id == book.id, BookCopy.status == CopyStatus.available)
        )).scalar_one()
    db.add(AuditLog(
        admin_id=admin.id, action="copy_inventory_updated", resource="book_copy", resource_id=copy.id,
        details=f"from={previous_status}; to={payload.status}; note={payload.note or ''}",
    ))
    await db.commit()
    catalog_cache.invalidate()
    return {"id": copy.id, "status": copy.status.value, "available_copies": book.available_copies if book else 0}


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
        category=payload.category,
        language=payload.language,
        publisher=payload.publisher,
        edition=payload.edition,
        shelf_location=payload.shelf_location,
        total_copies=payload.total_copies,
        available_copies=payload.total_copies,
        cover_url=payload.cover_url,
        description=payload.description,
    )
    db.add(book)
    await db.flush()
    await add_copies(db, book, payload.total_copies)
    await db.commit()
    await db.refresh(book)
    catalog_cache.invalidate()
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
        if diff < 0:
            copies = (await db.execute(
                select(BookCopy)
                .where(BookCopy.book_id == book.id, BookCopy.status == CopyStatus.available)
                .order_by(BookCopy.copy_number.desc())
                .limit(-diff)
                .with_for_update()
            )).scalars().all()
            if len(copies) != -diff:
                raise HTTPException(status_code=400, detail="Available copy records do not match this book's inventory.")
            for copy in copies:
                copy.status = CopyStatus.withdrawn
        elif diff > 0:
            withdrawn = (await db.execute(
                select(BookCopy)
                .where(BookCopy.book_id == book.id, BookCopy.status == CopyStatus.withdrawn)
                .order_by(BookCopy.copy_number)
                .limit(diff)
                .with_for_update()
            )).scalars().all()
            for copy in withdrawn:
                copy.status = CopyStatus.available
            await add_copies(db, book, diff - len(withdrawn))
        book.available_copies += diff

    for field, value in update_data.items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)
    catalog_cache.invalidate()
    return book


@router.get("/{book_id}/copies", response_model=list[BookCopyOut])
async def list_book_copies(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List individually tracked copies for staff inventory checks."""
    if not await db.get(Book, book_id):
        raise HTTPException(status_code=404, detail="Book not found.")
    return (await db.execute(
        select(BookCopy).where(BookCopy.book_id == book_id).order_by(BookCopy.copy_number)
    )).scalars().all()


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
    catalog_cache.invalidate()
