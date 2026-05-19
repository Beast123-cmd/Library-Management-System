import re

with open("app_sqlite.py", "r") as f:
    code = f.read()

# Replace ? with %s in cursor.execute statements.
# This regex looks for string literals containing ? and replaces them with %s
# Actually, since it's SQL queries, replacing ? with %s globally in execute strings is fine.
# But it's safer to just replace '?' with '%s' in the entire file and manually fix any false positives.
# Let's see if there are any '?' not in SQL queries.
# E.g. "publish_year = COALESCE(?, publish_year)" -> "publish_year = COALESCE(%s, publish_year)"

code = code.replace("sqlite3", "psycopg2")
code = code.replace("import psycopg2", "import psycopg2\nimport psycopg2.extras")

# Replace cursor = conn.cursor() with cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
code = code.replace("conn.cursor()", "conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)")

# Remove dict_factory related stuff
code = re.sub(r'def dict_factory.*?return d', '', code, flags=re.DOTALL)
code = code.replace("conn.row_factory = dict_factory", "")

# Replace ? with %s
code = code.replace("?", "%s")

# Fix get_db_connection
code = re.sub(r'def get_db_connection\(\):.*?return conn', '''DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_zyYesiKh2V0L@ep-raspy-meadow-akbv2n5w-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn''', code, flags=re.DOTALL)

with open("app_postgres.py", "w") as f:
    f.write(code)
