import re

with open("app_postgres.py", "r") as f:
    code = f.read()

# Replace init_db function with empty function
code = re.sub(r'def init_db\(\):.*?def login_required', 'def init_db():\n    pass\n\n# -------------------- DECORATORS --------------------\ndef login_required', code, flags=re.DOTALL)

with open("app_postgres.py", "w") as f:
    f.write(code)
