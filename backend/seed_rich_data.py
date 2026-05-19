import asyncio
import os
import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ASYNC_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Clean up query parameters that asyncpg doesn't support
if "?" in ASYNC_URL:
    base_url, query = ASYNC_URL.split("?", 1)
    params = query.split("&")
    clean_params = [p for p in params if not p.startswith("sslmode") and not p.startswith("channel_binding")]
    if clean_params:
        ASYNC_URL = base_url + "?" + "&".join(clean_params)
    else:
        ASYNC_URL = base_url

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    engine = create_async_engine(ASYNC_URL, echo=True)
    
    async with engine.begin() as conn:
        print("🌱 Seeding rich members and transactions data...")
        
        # 1. Check existing books
        books_res = await conn.execute(text("SELECT id, title, total_copies FROM books;"))
        books = books_res.all()
        if not books:
            print("❌ No books found in DB. Please run seed.py first to seed books.")
            await engine.dispose()
            return
            
        print(f"📚 Found {len(books)} books.")
        book_ids = [b[0] for b in books]
        book_map = {b[0]: {"title": b[1], "total": b[2]} for b in books}

        # 2. Seed members
        hashed_pw = pwd_context.hash("password123")
        members = [
            ("Aayush Sharma", "aayush@library.com", "aayush_s", hashed_pw, "member"),
            ("Priya Patel", "priya@library.com", "priya_p", hashed_pw, "member"),
            ("Aditya Verma", "aditya@library.com", "aditya_v", hashed_pw, "member"),
            ("Rohan Gupta", "rohan@library.com", "rohan_g", hashed_pw, "member"),
            ("Neha Iyer", "neha@library.com", "neha_i", hashed_pw, "member"),
            ("Vikram Singh", "vikram@library.com", "vikram_s", hashed_pw, "member")
        ]
        
        print("🗑️ Cleaning up existing transactions and members...")
        await conn.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE;"))
        await conn.execute(text("DELETE FROM users WHERE role = 'member';"))
        
        for name, email, username, pw, role in members:
            await conn.execute(text("""
                INSERT INTO users (name, email, username, hashed_password, role)
                VALUES (:name, :email, :username, :pw, :role)
                ON CONFLICT (username) DO NOTHING;
            """), {"name": name, "email": email, "username": username, "pw": pw, "role": role})
            
        # Get users from DB
        users_res = await conn.execute(text("SELECT id, name, username FROM users WHERE role = 'member';"))
        member_users = users_res.all()
        member_ids = [u[0] for u in member_users]
        print(f"✅ Seeding completed. Found {len(member_users)} active member accounts.")

        # 3. Create transactions
        print("🗑️ Reset existing transactions to seed realistic historical trends.")

        # Let's seed transactions across the last 6 months:
        # Dec 2025, Jan 2026, Feb 2026, Mar 2026, Apr 2026, May 2026
        today = datetime.date.today()
        
        # We need a list of transactions with issue and return dates
        txns_to_seed = [
            # Dec 2025
            {"user_idx": 0, "book_idx": 0, "issue_days_ago": 160, "return_days_ago": 145, "status": "returned"},
            {"user_idx": 1, "book_idx": 1, "issue_days_ago": 155, "return_days_ago": 140, "status": "returned"},
            {"user_idx": 2, "book_idx": 2, "issue_days_ago": 150, "return_days_ago": 135, "status": "returned"},
            
            # Jan 2026
            {"user_idx": 0, "book_idx": 3, "issue_days_ago": 130, "return_days_ago": 115, "status": "returned"},
            {"user_idx": 3, "book_idx": 4, "issue_days_ago": 125, "return_days_ago": 110, "status": "returned"},
            {"user_idx": 4, "book_idx": 5, "issue_days_ago": 120, "return_days_ago": 105, "status": "returned"},
            {"user_idx": 1, "book_idx": 0, "issue_days_ago": 118, "return_days_ago": 108, "status": "returned"},
            
            # Feb 2026
            {"user_idx": 2, "book_idx": 6, "issue_days_ago": 95, "return_days_ago": 80, "status": "returned"},
            {"user_idx": 5, "book_idx": 7, "issue_days_ago": 90, "return_days_ago": 75, "status": "returned"},
            {"user_idx": 0, "book_idx": 8, "issue_days_ago": 88, "return_days_ago": 73, "status": "returned"},
            {"user_idx": 3, "book_idx": 1, "issue_days_ago": 85, "return_days_ago": 70, "status": "returned"},
            
            # Mar 2026
            {"user_idx": 1, "book_idx": 2, "issue_days_ago": 68, "return_days_ago": 53, "status": "returned"},
            {"user_idx": 4, "book_idx": 3, "issue_days_ago": 65, "return_days_ago": 50, "status": "returned"},
            {"user_idx": 2, "book_idx": 4, "issue_days_ago": 60, "return_days_ago": 45, "status": "returned"},
            {"user_idx": 5, "book_idx": 5, "issue_days_ago": 58, "return_days_ago": 43, "status": "returned"},
            {"user_idx": 0, "book_idx": 6, "issue_days_ago": 55, "return_days_ago": 40, "status": "returned"},
            
            # Apr 2026
            {"user_idx": 3, "book_idx": 7, "issue_days_ago": 40, "return_days_ago": 25, "status": "returned"},
            {"user_idx": 1, "book_idx": 8, "issue_days_ago": 38, "return_days_ago": 23, "status": "returned"},
            {"user_idx": 2, "book_idx": 9, "issue_days_ago": 35, "return_days_ago": 20, "status": "returned"},
            {"user_idx": 0, "book_idx": 0, "issue_days_ago": 32, "return_days_ago": 18, "status": "returned"},
            {"user_idx": 4, "book_idx": 1, "issue_days_ago": 30, "return_days_ago": 15, "status": "returned"},
            
            # May 2026 (Active & Overdue Issues)
            # Active issues (not returned, expected return date in the future)
            {"user_idx": 0, "book_idx": 2, "issue_days_ago": 10, "return_days_ago": None, "status": "issued"},
            {"user_idx": 0, "book_idx": 3, "issue_days_ago": 8,  "return_days_ago": None, "status": "issued"},
            {"user_idx": 1, "book_idx": 4, "issue_days_ago": 7,  "return_days_ago": None, "status": "issued"},
            {"user_idx": 1, "book_idx": 5, "issue_days_ago": 5,  "return_days_ago": None, "status": "issued"},
            {"user_idx": 2, "book_idx": 6, "issue_days_ago": 4,  "return_days_ago": None, "status": "issued"},
            {"user_idx": 3, "book_idx": 7, "issue_days_ago": 3,  "return_days_ago": None, "status": "issued"},
            {"user_idx": 4, "book_idx": 8, "issue_days_ago": 2,  "return_days_ago": None, "status": "issued"},
            
            # Overdue issues (not returned, expected return date in the past)
            {"user_idx": 5, "book_idx": 9, "issue_days_ago": 25, "return_days_ago": None, "status": "issued"}
        ]

        # In-memory counter of issued books to adjust available_copies
        issued_counts = {bid: 0 for bid in book_ids}

        print("🔄 Seeding transactions...")
        for tx in txns_to_seed:
            user_id = member_ids[tx["user_idx"] % len(member_ids)]
            book_id = book_ids[tx["book_idx"] % len(book_ids)]
            
            issue_date = today - datetime.timedelta(days=tx["issue_days_ago"])
            expected_return_date = issue_date + datetime.timedelta(days=14)
            
            if tx["return_days_ago"] is not None:
                actual_return_date = today - datetime.timedelta(days=tx["return_days_ago"])
            else:
                actual_return_date = None
                # Book is currently out
                issued_counts[book_id] += 1
                
            await conn.execute(text("""
                INSERT INTO transactions (user_id, book_id, issue_date, expected_return_date, actual_return_date, status, fine_amount)
                VALUES (:user_id, :book_id, :issue_date, :expected_return_date, :actual_return_date, :status, :fine_amount)
            """), {
                "user_id": user_id,
                "book_id": book_id,
                "issue_date": issue_date,
                "expected_return_date": expected_return_date,
                "actual_return_date": actual_return_date,
                "status": tx["status"],
                "fine_amount": 15.0 if tx["status"] == "issued" and expected_return_date < today else 0.0
            })

        print("📋 Adjusting book available_copies based on current issues...")
        for book_id, count in issued_counts.items():
            total = book_map[book_id]["total"]
            avail = max(0, total - count)
            await conn.execute(text("""
                UPDATE books SET available_copies = :avail WHERE id = :id;
            """), {"avail": avail, "id": book_id})

        print("✅ Databases populated successfully with active transactions!")

    await engine.dispose()
    print("🎉 Rich seeding complete!")

if __name__ == "__main__":
    asyncio.run(main())
