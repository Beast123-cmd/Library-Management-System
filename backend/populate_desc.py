import os
import requests
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_zyYesiKh2V0L@ep-raspy-meadow-akbv2n5w-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DATABASE_URL)

def get_desc_for_isbn(isbn):
    if not isbn: return None
    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=details&format=json"
        res = requests.get(url, timeout=5)
        if res.ok:
            data = res.json()
            book_data = data.get(f"ISBN:{isbn}")
            if book_data and 'details' in book_data:
                details = book_data['details']
                if 'description' in details:
                    desc = details['description']
                    return desc if isinstance(desc, str) else desc.get('value')
                elif 'works' in details and len(details['works']) > 0:
                    work_key = details['works'][0]['key']
                    work_res = requests.get(f"https://openlibrary.org{work_key}.json", timeout=5)
                    if work_res.ok:
                        work_data = work_res.json()
                        if 'description' in work_data:
                            desc = work_data['description']
                            return desc if isinstance(desc, str) else desc.get('value')
    except Exception as e:
        print(f"Error fetching {isbn}: {e}")
    return None

with engine.begin() as conn:
    books = conn.execute(text("SELECT id, isbn FROM books WHERE description IS NULL")).fetchall()
    for b in books:
        desc = get_desc_for_isbn(b.isbn)
        if desc:
            conn.execute(text("UPDATE books SET description = :desc WHERE id = :id"), {"desc": desc, "id": b.id})
            print(f"Updated description for book ID {b.id}")
        else:
            print(f"No description found for book ID {b.id}")
