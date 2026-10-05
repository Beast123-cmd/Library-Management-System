import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.database import get_db
from app.models.models import Book, Transaction, User
from app.core.dependencies import get_current_admin
import datetime
from calendar import month_abbr
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_analytics_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Retrieve dynamic analytics metrics for charts."""
    
    # 1. Transaction Flow (last 6 months)
    today = datetime.date.today()
    months = []
    # Calculate months backward to maintain chronological order
    for i in range(5, -1, -1):
        # Subtracting days dynamically, handles year boundaries cleanly
        d = today - datetime.timedelta(days=i*30)
        months.append((d.year, d.month, month_abbr[d.month]))
        
    trend_dict = {m[2]: {"issues": 0, "returns": 0} for m in months}
    six_months_ago = today - datetime.timedelta(days=180)
    
    result = await db.execute(
        select(Transaction.issue_date, Transaction.actual_return_date)
        .where(Transaction.issue_date >= six_months_ago)
    )
    for row in result.all():
        issue_date, return_date = row[0], row[1]
        
        issue_month = month_abbr[issue_date.month]
        if issue_month in trend_dict:
            trend_dict[issue_month]["issues"] += 1
            
        if return_date:
            return_month = month_abbr[return_date.month]
            if return_month in trend_dict:
                trend_dict[return_month]["returns"] += 1
                
    trend_list = [{"name": name, "issues": data["issues"], "returns": data["returns"]} for name, data in trend_dict.items()]

    # 2. Real catalogue distribution based on the librarian's categories.
    category_rows = (await db.execute(
        select(func.coalesce(Book.category, "Uncategorized"), func.count(Book.id))
        .group_by(func.coalesce(Book.category, "Uncategorized"))
        .order_by(desc(func.count(Book.id)))
        .limit(6)
    )).all()
    total = sum(row[1] for row in category_rows) or 1
    colors = ["#6366f1", "#a855f7", "#06b6d4", "#10b981", "#f59e0b", "#ec4899"]
    category_list = [
        {"name": name, "value": round((count / total) * 100, 1), "color": colors[index % len(colors)]}
        for index, (name, count) in enumerate(category_rows)
    ]

    # 3. Top Circulated Books
    top_books_result = await db.execute(
        select(Book.title, func.count(Transaction.id).label("txn_count"))
        .join(Transaction, Book.id == Transaction.book_id)
        .group_by(Book.id, Book.title)
        .order_by(desc("txn_count"))
        .limit(5)
    )
    top_books_list = [{"name": r[0], "count": r[1]} for r in top_books_result.all()]

    return {
        "transactionTrendData": trend_list,
        "categoryData": category_list,
        "topBooksData": top_books_list
    }


@router.get("/export")
async def export_analytics(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Download a compact CSV report containing the current operational metrics."""
    stats = await get_analytics_stats(db, current_admin)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "label", "value"])
    writer.writerow(["summary", "Generated on", datetime.date.today().isoformat()])
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
