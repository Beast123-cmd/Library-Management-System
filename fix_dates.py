with open("app_postgres.py", "r") as f:
    code = f.read()

code = code.replace("date('now')", "CURRENT_DATE")
code = code.replace("date('now', '-12 months')", "CURRENT_DATE - INTERVAL '12 months'")
code = code.replace("strftime('%Y-%m', issue_date)", "to_char(issue_date, 'YYYY-MM')")

with open("app_postgres.py", "w") as f:
    f.write(code)
