"""
One-time database initialization script.
Creates all tables and seeds an admin user.
Run: source venv/bin/activate && python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
# Convert to asyncpg URL and strip parameters that asyncpg doesn't support
# asyncpg supports ssl=True rather than sslmode=require as a direct parameter, 
# but when using connection strings we can just remove sslmode=require since it defaults to secure or we can handle it via ssl context.
ASYNC_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
# Let's clean up any query parameters that asyncpg doesn't like:
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
        print("🔧 Creating tables...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                username VARCHAR(80) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'member' NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(150) NOT NULL,
                isbn VARCHAR(20) UNIQUE,
                publish_year INTEGER,
                total_copies INTEGER DEFAULT 1 NOT NULL,
                available_copies INTEGER DEFAULT 1 NOT NULL,
                cover_url VARCHAR(500),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) NOT NULL,
                book_id INTEGER REFERENCES books(id) NOT NULL,
                issue_date DATE NOT NULL,
                expected_return_date DATE NOT NULL,
                actual_return_date DATE,
                status VARCHAR(20) DEFAULT 'issued' NOT NULL,
                fine_amount FLOAT DEFAULT 0.0
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                resource VARCHAR(100),
                resource_id INTEGER,
                details TEXT,
                ip_address VARCHAR(45),
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        """))

        # Add indexes
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);"))

        print("✅ Tables created successfully!")

        # Seed admin user
        admin_password = pwd_context.hash("admin123")
        await conn.execute(text("""
            INSERT INTO users (name, email, username, hashed_password, role)
            VALUES ('Administrator', 'admin@library.com', 'admin', :password, 'admin')
            ON CONFLICT (username) DO NOTHING;
        """), {"password": admin_password})

        # Seed sample books
        await conn.execute(text("""
            INSERT INTO books (title, author, isbn, publish_year, total_copies, available_copies) VALUES
            ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 1925, 5, 5),
            ('To Kill a Mockingbird', 'Harper Lee', '9780061935466', 1960, 3, 3),
            ('1984', 'George Orwell', '9780451524935', 1949, 4, 4),
            ('Pride and Prejudice', 'Jane Austen', '9780141439518', 1813, 6, 6),
            ('The Catcher in the Rye', 'J.D. Salinger', '9780316769174', 1951, 2, 2),
            ('Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', '9780590353427', 1997, 8, 8),
            ('The Alchemist', 'Paulo Coelho', '9780062315007', 1988, 5, 5),
            ('Atomic Habits', 'James Clear', '9780735211292', 2018, 4, 4),
            ('Clean Code', 'Robert C. Martin', '9780132350884', 2008, 3, 3),
            ('The Pragmatic Programmer', 'Andrew Hunt', '9780201616224', 1999, 2, 2)
            ON CONFLICT (isbn) DO NOTHING;
        """))

        print("✅ Admin user seeded: username=admin, password=admin123")
        print("✅ 10 sample books seeded!")

    await engine.dispose()
    print("\n🎉 Database ready! You can now login at http://localhost:3000/login")


if __name__ == "__main__":
    asyncio.run(main())
