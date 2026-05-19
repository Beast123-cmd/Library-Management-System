import asyncio
import aiohttp
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.models import Book
from app.core.config import settings

async def update_books():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        
        async with aiohttp.ClientSession() as client:
            for book in books:
                if not book.cover_url and book.isbn:
                    print(f"Fetching metadata for {book.title} (ISBN: {book.isbn})")
                    clean_isbn = book.isbn.replace("-", "").strip()
                    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data"
                    async with client.get(url) as resp:
                        data = await resp.json()
                        book_data = data.get(f"ISBN:{clean_isbn}")
                        if book_data:
                            if book_data.get("cover") and book_data["cover"].get("large"):
                                book.cover_url = book_data["cover"]["large"]
                            elif book_data.get("cover") and book_data["cover"].get("medium"):
                                book.cover_url = book_data["cover"]["medium"]
                            
                            if book_data.get("publish_date"):
                                import re
                                year_match = re.search(r'\d{4}', book_data["publish_date"])
                                if year_match:
                                    book.publish_year = int(year_match.group(0))
                            
                            print(f"Updated {book.title} cover_url to {book.cover_url}")
                            session.add(book)
        await session.commit()
    print("Done updating books.")

if __name__ == "__main__":
    asyncio.run(update_books())
