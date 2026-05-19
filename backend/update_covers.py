import sys
import os
import requests
import re

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.models.models import Book
from app.core.config import settings

def update_books():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        books = session.scalars(select(Book)).all()
        
        for book in books:
            if not book.cover_url:
                search_query = ""
                if book.isbn:
                    search_query = f"bibkeys=ISBN:{book.isbn.replace('-', '').strip()}"
                else:
                    title_query = "+".join(book.title.split())
                    search_query = f"title={title_query}"
                    
                print(f"Fetching metadata for {book.title}...")
                search_url = f"https://openlibrary.org/search.json?title={'+'.join(book.title.split())}&limit=1"
                try:
                    resp = requests.get(search_url)
                    data = resp.json()
                    if data.get("docs") and len(data["docs"]) > 0:
                        doc = data["docs"][0]
                        
                        if doc.get("cover_i"):
                            book.cover_url = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                        
                        if not book.isbn and doc.get("isbn") and len(doc["isbn"]) > 0:
                            book.isbn = doc["isbn"][0]
                            
                        if not book.publish_year and doc.get("first_publish_year"):
                            book.publish_year = doc["first_publish_year"]
                            
                        print(f"Updated {book.title} metadata. Cover: {book.cover_url}")
                        session.add(book)
                except Exception as e:
                    print(f"Failed to update {book.title}: {e}")
                    
        session.commit()
    print("Done updating books.")

if __name__ == "__main__":
    update_books()
