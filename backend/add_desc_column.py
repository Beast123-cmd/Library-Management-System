import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_zyYesiKh2V0L@ep-raspy-meadow-akbv2n5w-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS description TEXT;"))
    print("Added description column to books table")
