import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.database import get_db
from app.models.models import Book, FinePayment, Transaction, TransactionStatus, User
from app.core.dependencies import get_current_admin
import datetime
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_analytics_stats(
    days: int = Query(180, ge=30, le=365),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Retrieve dynamic analytics metrics for charts."""
    
    # 1. Period circulation flow, grouped into six equally sized buckets.
    today = datetime.date.today()
    period_start = today - datetime.timedelta(days=days - 1)
    bucket_days = max(1, (days + 5) // 6)
    buckets = [period_start + datetime.timedelta(days=index * bucket_days) for index in range(6)]
    trend_list = [{"name": bucket.strftime("%d %b"), "issues": 0, "returns": 0} for bucket in buckets]
    result = await db.execute(
        select(Transaction.issue_date, Transaction.actual_return_date)
        .where((Transaction.issue_date >= period_start) | (Transaction.actual_return_date >= period_start))
    )
    for row in result.all():
        issue_date, return_date = row[0], row[1]
        for value, key in ((issue_date, "issues"), (return_date, "returns")):
            if value and value >= period_start:
                index = min((value - period_start).days // bucket_days, len(trend_list) - 1)
                trend_list[index][key] += 1

    # 2. Real catalogue distribution based on the librarian's categories.
    category_rows = (await db.execute(
        select(Book.category, func.count(Book.id))
        .group_by(Book.category)
        .order_by(desc(func.count(Book.id)))
        .limit(6)
    )).all()
    total = sum(row[1] for row in category_rows) or 1
    colors = ["#6366f1", "#a855f7", "#06b6d4", "#10b981", "#f59e0b", "#ec4899"]
    category_list = [
        {"name": name or "Uncategorized", "value": round((count / total) * 100, 1), "color": colors[index % len(colors)]}
        for index, (name, count) in enumerate(category_rows)
    ]

    # 3. Top Circulated Books
    top_books_result = await db.execute(
        select(Book.title, func.count(Transaction.id).label("txn_count"))
        .join(Transaction, Book.id == Transaction.book_id)
        .where(Transaction.issue_date >= period_start)
        .group_by(Book.id, Book.title)
        .order_by(desc("txn_count"))
        .limit(5)
    )
    top_books_list = [{"name": r[0], "count": r[1]} for r in top_books_result.all()]

    issued_count = (await db.execute(select(func.count()).select_from(Transaction).where(Transaction.issue_date >= period_start))).scalar_one()
    returned_count = (await db.execute(select(func.count()).select_from(Transaction).where(Transaction.actual_return_date >= period_start))).scalar_one()
    overdue_count = (await db.execute(select(func.count()).select_from(Transaction).where(Transaction.status == TransactionStatus.issued, Transaction.expected_return_date < today))).scalar_one()
    outstanding_fines = (await db.execute(
        select(func.coalesce(func.sum(Transaction.fine_amount - func.coalesce(FinePayment.amount, 0.0)), 0.0))
        .outerjoin(FinePayment, FinePayment.transaction_id == Transaction.id)
        .where(Transaction.status == TransactionStatus.returned, Transaction.fine_amount > 0)
    )).scalar_one()
    total_copies, available_copies = (await db.execute(
        select(func.coalesce(func.sum(Book.total_copies), 0), func.coalesce(func.sum(Book.available_copies), 0))
    )).one()

    return {
        "periodDays": days,
        "summary": {
            "issued": issued_count, "returned": returned_count, "overdue": overdue_count,
            "outstandingFines": float(outstanding_fines), "totalCopies": total_copies, "availableCopies": available_copies,
        },
        "transactionTrendData": trend_list,
        "categoryData": category_list,
        "topBooksData": top_books_list
    }


@router.get("/export")
async def export_analytics(
    days: int = Query(180, ge=30, le=365),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Download a compact CSV report containing the current operational metrics."""
    stats = await get_analytics_stats(days, db, current_admin)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "label", "value"])
    writer.writerow(["summary", "Generated on", datetime.date.today().isoformat()])
    writer.writerow(["summary", "Reporting period", f"Last {days} days"])
    for label, value in stats["summary"].items():
        writer.writerow(["period summary", label, value])
    writer.writerow(["summary", "Total titles", (await db.execute(select(func.count()).select_from(Book))).scalar_one()])
    writer.writerow(["summary", "Total members", (await db.execute(select(func.count()).select_from(User))).scalar_one()])
    writer.writerow(["summary", "Total transactions", (await db.execute(select(func.count()).select_from(Transaction))).scalar_one()])
    for point in stats["transactionTrendData"]:
        writer.writerow(["monthly circulation", point["name"], f"Issued: {point['issues']}; Returned: {point['returns']}"])
    for category in stats["categoryData"]:
        writer.writerow(["catalogue category", category["name"], f"{category['value']}%"])
    for book in stats["topBooksData"]:
        writer.writerow(["top circulated books", book["name"], book["count"]])
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="library-analytics-report.csv"'},
    )


@router.get("/export/{report_type}")
async def export_operational_report(
    report_type: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Download the three operational reports staff use day to day."""
    output = io.StringIO()
    writer = csv.writer(output)
    today = datetime.date.today()

    if report_type == "overdue":
        writer.writerow(["transaction_id", "member", "email", "book", "due_date", "days_overdue", "estimated_fine"])
        rows = (await db.execute(
            select(Transaction, User.name, User.email, Book.title)
            .join(User, Transaction.user_id == User.id).join(Book, Transaction.book_id == Book.id)
            .where(Transaction.status.in_([TransactionStatus.issued, TransactionStatus.overdue]), Transaction.expected_return_date < today)
            .order_by(Transaction.expected_return_date)
        )).all()
        for transaction, name, email, title in rows:
            days = (today - transaction.expected_return_date).days
            fine = days * 5 if days <= 15 else 75 + (days - 15) * 50
            writer.writerow([transaction.id, name, email, title, transaction.expected_return_date, days, f"{fine:.2f}"])
    elif report_type == "fines":
        writer.writerow(["transaction_id", "member", "book", "assessed_amount", "paid_amount", "outstanding_amount", "received_at", "note"])
        rows = (await db.execute(
            select(Transaction, User.name, Book.title, FinePayment)
            .join(User, Transaction.user_id == User.id).join(Book, Transaction.book_id == Book.id)
            .outerjoin(FinePayment, FinePayment.transaction_id == Transaction.id)
            .where(Transaction.status == TransactionStatus.returned, Transaction.fine_amount > 0)
            .order_by(Transaction.actual_return_date.desc())
        )).all()
        for transaction, name, title, payment in rows:
            paid = payment.amount if payment else 0.0
            writer.writerow([transaction.id, name, title, f"{transaction.fine_amount:.2f}", f"{paid:.2f}", f"{transaction.fine_amount - paid:.2f}", payment.received_at if payment else "", payment.note if payment else ""])
    elif report_type == "inventory":
        writer.writerow(["book_id", "title", "author", "category", "shelf_location", "total_copies", "available_copies", "availability"])
        rows = (await db.execute(select(Book).order_by(Book.title))).scalars().all()
        for book in rows:
            availability = "out of stock" if book.available_copies == 0 else "low stock" if book.available_copies <= 2 else "available"
            writer.writerow([book.id, book.title, book.author, book.category or "", book.shelf_location or "", book.total_copies, book.available_copies, availability])
    else:
        raise HTTPException(status_code=404, detail="Report not found.")

    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="library-{report_type}-report.csv"'},
    )
