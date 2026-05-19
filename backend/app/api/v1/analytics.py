from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.database import get_db
from app.models.models import Book, Transaction, User
from app.core.dependencies import get_current_user
import datetime
from calendar import month_abbr
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_analytics_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

    # 2. Book Genre Distribution (in-memory heuristic classification)
    books_result = await db.execute(select(Book.title))
    books = books_result.scalars().all()
    
    categories = {
        "Fiction": 0,
        "Science & Tech": 0,
        "History & Bio": 0,
        "Self-Help": 0
    }
    
    for title in books:
        t = title.lower()
        if any(w in t for w in ["great", "mockingbird", "1984", "orwell", "potter", "alchemist", "gatsby", "pride", "catcher", "jane", "stone"]):
            categories["Fiction"] += 1
        elif any(w in t for w in ["clean", "code", "programming", "javascript", "python", "sql", "pragmatic", "design", "patterns", "refactoring"]):
            categories["Science & Tech"] += 1
        elif any(w in t for w in ["steve", "jobs", "sapiens", "biography", "history", "empire", "civilization", "historical"]):
            categories["History & Bio"] += 1
        else:
            categories["Self-Help"] += 1
            
    total = len(books) or 1
    category_list = [
        {"name": "Fiction", "value": round((categories["Fiction"] / total) * 100, 1), "color": "#6366f1"},
        {"name": "Science & Tech", "value": round((categories["Science & Tech"] / total) * 100, 1), "color": "#a855f7"},
        {"name": "History & Bio", "value": round((categories["History & Bio"] / total) * 100, 1), "color": "#06b6d4"},
        {"name": "Self-Help", "value": round((categories["Self-Help"] / total) * 100, 1), "color": "#10b981"},
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
