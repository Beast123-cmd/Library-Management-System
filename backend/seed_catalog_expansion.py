"""Add 50 distinct catalogue titles and 200 physical copies without deleting data.

Run from backend: venv/bin/python seed_catalog_expansion.py
"""

import asyncio

from sqlalchemy import select

from app.core.copies import add_copies
from app.db.database import AsyncSessionLocal, engine
from app.models.models import AuditLog, Book


# title, author, isbn, year, category, publisher, shelf
CATALOG = [
    ("Tomorrow, and Tomorrow, and Tomorrow", "Gabrielle Zevin", "9780593321201", 2022, "Contemporary Fiction", "Knopf", "A-10"),
    ("Circe", "Madeline Miller", "9780316556347", 2018, "Mythology", "Little, Brown", "A-11"),
    ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid", "9781501161933", 2017, "Contemporary Fiction", "Atria", "A-12"),
    ("Lessons in Chemistry", "Bonnie Garmus", "9780385547345", 2022, "Historical Fiction", "Doubleday", "A-13"),
    ("Demon Copperhead", "Barbara Kingsolver", "9780063251922", 2022, "Literary Fiction", "Harper", "A-14"),
    ("The Thursday Murder Club", "Richard Osman", "9781984880987", 2020, "Mystery", "Pamela Dorman", "A-15"),
    ("The Guest List", "Lucy Foley", "9780062868930", 2020, "Mystery", "William Morrow", "A-16"),
    ("The House in the Cerulean Sea", "TJ Klune", "9781250217318", 2020, "Fantasy", "Tor", "A-17"),
    ("Pachinko", "Min Jin Lee", "9781455563937", 2017, "Historical Fiction", "Grand Central", "A-18"),
    ("The Vanishing Half", "Brit Bennett", "9780525536291", 2020, "Contemporary Fiction", "Riverhead", "A-19"),
    ("Anxious People", "Fredrik Backman", "9781501160837", 2019, "Contemporary Fiction", "Atria", "A-20"),
    ("Normal People", "Sally Rooney", "9781984822185", 2019, "Literary Fiction", "Hogarth", "A-21"),
    ("Station Eleven", "Emily St. John Mandel", "9780804172448", 2014, "Science Fiction", "Vintage", "A-22"),
    ("The Martian", "Andy Weir", "9780553418026", 2014, "Science Fiction", "Crown", "A-23"),
    ("Never Let Me Go", "Kazuo Ishiguro", "9781400078776", 2005, "Science Fiction", "Vintage", "A-24"),
    ("The Name of the Wind", "Patrick Rothfuss", "9780756404741", 2007, "Fantasy", "DAW", "A-25"),
    ("The Priory of the Orange Tree", "Samantha Shannon", "9781635570298", 2019, "Fantasy", "Bloomsbury", "A-26"),
    ("The Invisible Life of Addie LaRue", "V. E. Schwab", "9780765387561", 2020, "Fantasy", "Tor", "A-27"),
    ("The Book Thief", "Markus Zusak", "9780375842207", 2005, "Historical Fiction", "Knopf", "A-28"),
    ("A Man Called Ove", "Fredrik Backman", "9781476738024", 2012, "Contemporary Fiction", "Atria", "A-29"),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "9780374533557", 2011, "Psychology", "Farrar, Straus and Giroux", "B-10"),
    ("Range", "David Epstein", "9780735214484", 2019, "Business", "Riverhead", "B-11"),
    ("The Lean Startup", "Eric Ries", "9780307887894", 2011, "Business", "Crown", "B-12"),
    ("Good Strategy Bad Strategy", "Richard Rumelt", "9780307886231", 2011, "Business", "Crown Currency", "B-13"),
    ("Start With Why", "Simon Sinek", "9781591846444", 2009, "Leadership", "Portfolio", "B-14"),
    ("Measure What Matters", "John Doerr", "9780525536222", 2018, "Leadership", "Portfolio", "B-15"),
    ("The Culture Code", "Daniel Coyle", "9780525492467", 2018, "Leadership", "Bantam", "B-16"),
    ("Essentialism", "Greg McKeown", "9780804137386", 2014, "Productivity", "Crown Currency", "B-17"),
    ("Four Thousand Weeks", "Oliver Burkeman", "9780374159122", 2021, "Productivity", "Farrar, Straus and Giroux", "B-18"),
    ("The Checklist Manifesto", "Atul Gawande", "9780805091748", 2010, "Productivity", "Metropolitan", "B-19"),
    ("Refactoring", "Martin Fowler", "9780134757599", 2018, "Technology", "Addison-Wesley", "C-10"),
    ("Domain-Driven Design", "Eric Evans", "9780321125217", 2003, "Technology", "Addison-Wesley", "C-11"),
    ("The Pragmatic Programmer: 20th Anniversary Edition", "David Thomas", "9780135957059", 2019, "Technology", "Addison-Wesley", "C-12"),
    ("Don't Make Me Think", "Steve Krug", "9780321965516", 2013, "Design", "New Riders", "C-13"),
    ("Hooked", "Nir Eyal", "9781591847786", 2014, "Design", "Portfolio", "C-14"),
    ("Sprint", "Jake Knapp", "9781501121746", 2016, "Design", "Simon & Schuster", "C-15"),
    ("Inspired", "Marty Cagan", "9781119387503", 2017, "Product Management", "Wiley", "C-16"),
    ("The Mom Test", "Rob Fitzpatrick", "9781492180746", 2013, "Product Management", "CreateSpace", "C-17"),
    ("Fundamentals of Data Visualization", "Claus O. Wilke", "9781492031086", 2019, "Data", "O'Reilly Media", "C-18"),
    ("The Information", "James Gleick", "9781400096237", 2011, "Science", "Pantheon", "D-10"),
    ("Cosmos", "Carl Sagan", "9780345539434", 2013, "Science", "Ballantine", "D-11"),
    ("The Gene", "Siddhartha Mukherjee", "9781476733524", 2016, "Science", "Scribner", "D-12"),
    ("The Body", "Bill Bryson", "9780385539302", 2019, "Science", "Doubleday", "D-13"),
    ("The Wright Brothers", "David McCullough", "9781476728742", 2015, "History", "Simon & Schuster", "D-14"),
    ("The Silk Roads", "Peter Frankopan", "9781101912379", 2015, "History", "Knopf", "D-15"),
    ("Braiding Sweetgrass", "Robin Wall Kimmerer", "9781571313560", 2013, "Nature", "Milkweed", "D-16"),
    ("The Anthropocene Reviewed", "John Green", "9780525555216", 2021, "Essays", "Dutton", "D-17"),
    ("Why We Sleep", "Matthew Walker", "9781501144318", 2017, "Wellbeing", "Scribner", "E-10"),
    ("The Comfort Book", "Matt Haig", "9780143136668", 2021, "Wellbeing", "Penguin", "E-11"),
    ("Maybe You Should Talk to Someone", "Lori Gottlieb", "9781328662057", 2019, "Psychology", "Houghton Mifflin", "E-12"),
]


async def main():
    async with AsyncSessionLocal() as db:
        marker = await db.execute(select(AuditLog.id).where(AuditLog.action == "catalog_expansion_seeded"))
        if marker.scalar_one_or_none():
            print("Catalog expansion already exists; no changes made.")
            return

        inserted = 0
        copies_added = 0
        for title, author, isbn, year, category, publisher, shelf in CATALOG:
            if (await db.execute(select(Book.id).where(Book.isbn == isbn))).scalar_one_or_none():
                continue
            book = Book(
                title=title, author=author, isbn=isbn, publish_year=year,
                category=category, language="English", publisher=publisher,
                shelf_location=shelf, total_copies=4, available_copies=4,
                cover_url=f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
                description=f"A curated library copy of {title} by {author}.",
            )
            db.add(book)
            await db.flush()
            await add_copies(db, book, 4)
            inserted += 1
            copies_added += 4

        db.add(AuditLog(action="catalog_expansion_seeded", resource="system", details=f"Inserted {inserted} titles and {copies_added} physical copies"))
        await db.commit()
        print(f"Added {inserted} unique books and {copies_added} physical copies.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
