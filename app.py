# app.py (cleaned & fixed: uses books_new everywhere)

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, make_response
)
from collections import Counter
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import csv
import io
import json

app = Flask(__name__)
app.secret_key = "your_secret_key"  # replace with a secure secret in production
app.jinja_env.globals['datetime'] = datetime

# ---------- CONFIG ----------
FINE_PER_DAY = 5.00
DEFAULT_LOAN_DAYS = 7

# -------------------- DATABASE CONNECTION --------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="library_admin",
        password="libpass123",
        database="library_dbms"
    )

# -------------------- DECORATORS --------------------
def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return inner

def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required!", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return inner

# -------------------- SIGNUP --------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM members WHERE email=%s OR name=%s", (email, name))
        if cursor.fetchone():
            conn.close()
            flash("Member exists. Please login.", "warning")
            return redirect(url_for("login"))
        cursor.execute("INSERT INTO members (name, email) VALUES (%s, %s)", (name, email))
        member_id = cursor.lastrowid
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (name, hashed_password, "member")
        )
        conn.commit()
        conn.close()
        flash("Signup successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")

# -------------------- LOGIN --------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        conn.close()
        if not user or not check_password_hash(user["password"], password):
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))
        session["username"] = user["username"]
        session["role"] = user["role"]
        flash(f"Welcome, {user['username']}!", "success")
        return redirect(url_for("index"))
    return render_template("login.html")

# -------------------- INDEX --------------------
@app.route("/index")
@app.route("/dashboard")
@login_required
def index():
    return render_template("index.html", role=session.get("role"), username=session.get("username"))

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# -------------------- BOOKS --------------------
@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        total_copies = int(request.form.get("total_copies", 1))
        cursor.execute(
            "UPDATE books_new SET title=%s, author=%s, total_copies=%s WHERE book_id=%s",
            (title, author, total_copies, book_id)
        )
        conn.commit()
        conn.close()
        flash("Book updated.", "success")
        return redirect(url_for("books"))

    cursor.execute("SELECT * FROM books_new WHERE book_id=%s", (book_id,))
    book = cursor.fetchone()
    conn.close()
    return render_template("edit_book.html", book=book)

@app.route("/books/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_book():
    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        total_copies = int(request.form.get("total_copies", 1))
        if not title or not author:
            flash("Title and Author are required.", "danger")
            return redirect(url_for("add_book"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books_new (title, author, total_copies, available_copies) VALUES (%s, %s, %s, %s)",
            (title, author, total_copies, total_copies)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Book '{title}' added successfully!", "success")
        return redirect(url_for("books"))

    return render_template("add_book.html")

@app.route("/books")
@login_required
def books():
    q = request.args.get("q", "").strip()
    available_filter = request.args.get("available", "").strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM books_new"
    params = []

    if q:
        sql += " WHERE title LIKE %s OR author LIKE %s"
        like_q = f"%{q}%"
        params.extend([like_q, like_q])

    if available_filter == "1":
        if "WHERE" in sql:
            sql += " AND available_copies > 0"
        else:
            sql += " WHERE available_copies > 0"

    sql += " ORDER BY title"
    cursor.execute(sql, params)
    books_list = cursor.fetchall()
    
    # Calculate totals
    total_titles = len(books_list)
    total_copies = sum(book['total_copies'] for book in books_list)
    
    conn.close()
    return render_template("books.html", books=books_list, q=q, available_filter=available_filter, total_titles=total_titles, total_copies=total_copies)

# -------------------- ISSUE BOOK --------------------
@app.route("/books/issue/<int:book_id>", methods=["GET", "POST"])
@login_required
@admin_required
def issue_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch book details from books_new
    cursor.execute("SELECT * FROM books_new WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()

    if not book:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("books"))

    # If POST request → issue the book
    if request.method == "POST":
        member_id = request.form.get("member_id")
        due_days = int(request.form.get("due_days", DEFAULT_LOAN_DAYS))
        
        if not member_id:
            conn.close()
            flash("Please select a member.", "danger")
            return redirect(url_for("issue_book", book_id=book_id))

        # Check if available copies > 0
        if book["available_copies"] <= 0:
            flash("Book not available!", "danger")
            conn.close()
            return redirect(url_for("books"))

        # Check if member has reached the 5 book limit
        cursor.execute(
            "SELECT COUNT(*) as active_loans FROM transactions WHERE member_id=%s AND status='issued'",
            (member_id,)
        )
        active_loans = cursor.fetchone()["active_loans"]
        
        if active_loans >= 5:
            conn.close()
            flash("Member has reached the maximum limit of 5 books!", "danger")
            return redirect(url_for("issue_book", book_id=book_id))

        # Issue the book
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=due_days)

        cursor.execute(
            "INSERT INTO transactions (member_id, book_id, issue_date, due_date, status) "
            "VALUES (%s, %s, %s, %s, %s)",
            (member_id, book_id, issue_date, due_date, "issued")
        )

        cursor.execute(
            "UPDATE books_new SET available_copies = available_copies - 1 WHERE book_id = %s",
            (book_id,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Book issued successfully!", "success")
        return redirect(url_for("transactions"))

    # Fetch all members for the dropdown
    cursor.execute("SELECT member_id, name FROM members ORDER BY name")
    members = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template("issue_book.html", book=book, members=members)




# -------------------- RETURN BOOK --------------------
@app.route("/books/return/<int:txn_id>", methods=["POST"])
@login_required
@admin_required
def return_book(txn_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM transactions WHERE txn_id=%s", (txn_id,))
    txn = cursor.fetchone()
    if not txn or txn["status"] != "issued":
        conn.close()
        flash("Transaction invalid.", "warning")
        return redirect(url_for("transactions"))

    now = datetime.now()
    fine = 0.0
    if txn.get("due_date"):
        delta_days = (now.date() - txn["due_date"].date()).days
        if delta_days > 0:
            fine = round(delta_days * FINE_PER_DAY, 2)

    cursor.execute(
        "UPDATE transactions SET status='returned', return_date=%s, fine=%s WHERE txn_id=%s",
        (now, fine, txn_id)
    )
    cursor.execute(
        "UPDATE books_new SET available_copies = available_copies + 1 WHERE book_id=%s",
        (txn["book_id"],)
    )

    conn.commit()
    cursor.close()
    conn.close()
    flash(f"Book returned. Fine: {fine:.2f}" if fine > 0 else "Book returned successfully!", "success")
    return redirect(url_for("transactions"))

# -------------------- TRANSACTIONS --------------------
@app.route('/transactions')
@login_required
def transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session['role'] == 'admin':
        cursor.execute("""
            SELECT t.txn_id, 
                   m.name AS member_name, 
                   b.title AS book_title, 
                   t.issue_date, 
                   t.due_date, 
                   t.return_date, 
                   t.status, 
                   t.fine
            FROM transactions t
            JOIN members m ON t.member_id = m.member_id
            JOIN books_new b ON t.book_id = b.book_id
            ORDER BY t.issue_date DESC
        """)
    else:
        cursor.execute("SELECT member_id FROM members WHERE name=%s", (session["username"],))
        member = cursor.fetchone()
        if not member:
            conn.close()
            flash("Member record not found.", "danger")
            return redirect(url_for("index"))
        member_id = member["member_id"]

        cursor.execute("""
            SELECT t.txn_id, 
                   m.name AS member_name, 
                   b.title AS book_title, 
                   t.issue_date, 
                   t.due_date, 
                   t.return_date, 
                   t.status, 
                   t.fine
            FROM transactions t
            JOIN members m ON t.member_id = m.member_id
            JOIN books_new b ON t.book_id = b.book_id
            WHERE t.member_id = %s
            ORDER BY t.issue_date DESC
        """, (member_id,))

    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('transactions.html', transactions=transactions)

# -------------------- EXPORT CSV --------------------
@app.route("/transactions/export")
@login_required
@admin_required
def export_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.txn_id, m.name AS member_name, b.title AS book_title,
               t.issue_date, t.due_date, t.return_date, t.status, t.fine
        FROM transactions t
        JOIN members m ON t.member_id = m.member_id
        JOIN books_new b ON t.book_id = b.book_id
        ORDER BY t.issue_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Txn ID", "Member", "Book", "Issue Date", "Due Date", "Return Date", "Status", "Fine"])
    for r in rows:
        cw.writerow([
            r["txn_id"],
            r["member_name"],
            r["book_title"],
            r["issue_date"].strftime("%Y-%m-%d %H:%M:%S") if r["issue_date"] else "",
            r["due_date"].strftime("%Y-%m-%d %H:%M:%S") if r.get("due_date") else "",
            r["return_date"].strftime("%Y-%m-%d %H:%M:%S") if r.get("return_date") else "",
            r["status"],
            f"{r['fine']:.2f}"
        ])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    output.headers["Content-Type"] = "text/csv"
    return output

# -------------------- MEMBERS --------------------
@app.route("/members")
@login_required
@admin_required
def members():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT m.member_id, m.name, m.email,
               COUNT(t.txn_id) as total_loans,
               SUM(CASE WHEN t.status = 'issued' THEN 1 ELSE 0 END) as active_loans,
               SUM(CASE WHEN t.status = 'returned' THEN 1 ELSE 0 END) as completed_loans
        FROM members m
        LEFT JOIN transactions t ON m.member_id = t.member_id
        GROUP BY m.member_id, m.name, m.email
        ORDER BY m.name
    """)
    
    members = cursor.fetchall()
    conn.close()
    
    return render_template("members.html", members=members)

# -------------------- ADMIN DASHBOARD --------------------
@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT status, COUNT(*) AS count FROM transactions GROUP BY status")
    status_data = cursor.fetchall()
    pie_labels = [row["status"] for row in status_data]
    pie_values = [row["count"] for row in status_data]

    cursor.execute("""
        SELECT b.title, COUNT(*) AS times_issued
        FROM transactions t
        JOIN books_new b ON t.book_id = b.book_id
        WHERE t.status IN ('issued','returned')
        GROUP BY t.book_id
        ORDER BY times_issued DESC
        LIMIT 5
    """)
    top_books_data = cursor.fetchall()
    bar_labels = [row["title"] for row in top_books_data]
    bar_values = [row["times_issued"] for row in top_books_data]

    cursor.execute("""
        SELECT m.name AS member_name, b.title AS book_title, t.status, t.issue_date
        FROM transactions t
        JOIN members m ON t.member_id = m.member_id
        JOIN books_new b ON t.book_id = b.book_id
        ORDER BY t.issue_date DESC
        LIMIT 5
    """)
    recent_activities_data = cursor.fetchall()
    recent_activities = [
        f"{row['member_name']} {row['status']} '{row['book_title']}'"
        for row in recent_activities_data
    ]

    conn.close()
    return render_template(
        "dashboard.html",
        pie_labels=pie_labels,
        pie_values=pie_values,
        bar_labels=bar_labels,
        bar_values=bar_values,
        recent_activities=recent_activities
    )

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
