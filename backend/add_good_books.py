import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_zyYesiKh2V0L@ep-raspy-meadow-akbv2n5w-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DATABASE_URL)

books = [
    {
        "title": "The Lord of the Rings: The Fellowship of the Ring",
        "author": "J.R.R. Tolkien",
        "isbn": "9780544003415",
        "publish_year": 1954,
        "total_copies": 5,
        "available_copies": 5,
        "cover_url": "https://covers.openlibrary.org/b/id/8406786-L.jpg"
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441172719",
        "publish_year": 1965,
        "total_copies": 10,
        "available_copies": 10,
        "cover_url": "https://covers.openlibrary.org/b/id/13147152-L.jpg"
    },
    {
        "title": "The Hitchhiker's Guide to the Galaxy",
        "author": "Douglas Adams",
        "isbn": "9780345391803",
        "publish_year": 1979,
        "total_copies": 8,
        "available_copies": 8,
        "cover_url": "https://covers.openlibrary.org/b/id/8259431-L.jpg"
    },
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "isbn": "9780060935467",
        "publish_year": 1960,
        "total_copies": 15,
        "available_copies": 15,
        "cover_url": "https://covers.openlibrary.org/b/id/11186255-L.jpg"
    },
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "isbn": "9780141439471",
        "publish_year": 1818,
        "total_copies": 3,
        "available_copies": 3,
        "cover_url": "https://covers.openlibrary.org/b/id/8315185-L.jpg"
    }
]

with engine.begin() as conn:
    for book in books:
        res = conn.execute(text("SELECT id FROM books WHERE isbn = :isbn"), {"isbn": book["isbn"]}).fetchone()
        if not res:
            conn.execute(
                text("""
                INSERT INTO books (title, author, isbn, publish_year, total_copies, available_copies, cover_url)
                VALUES (:title, :author, :isbn, :publish_year, :total_copies, :available_copies, :cover_url)
                """),
                book
            )
            print(f"Inserted {book['title']}")
        else:
            print(f"Already exists: {book['title']}")
