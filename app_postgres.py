from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, make_response
)
from collections import Counter
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import csv
import io
import json
import os

# Custom row factory to convert datetime strings back to datetime objects


app = Flask(__name__)
app.secret_key = "your_secret_key"  # replace with a secure secret in production
app.jinja_env.globals['datetime'] = datetime
app.jinja_env.globals['now'] = datetime.now

# Jinja filter: safely format datetime or return as-is if already a string/empty
@app.template_filter('format_dt')
def format_dt(value):
    if not value:
        return ""
    # If it's already a string (SQLite often returns ISO strings), normalize lightly
    if isinstance(value, str):
        # Trim sub-second precision and replace 'T' with space if present
        normalized = value.replace('T', ' ')
        if '.' in normalized:
            normalized = normalized.split('.', 1)[0]
        return normalized
    # Try datetime formatting
    try:
        return value.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)

# ---------- CONFIG ----------
# Fine structure: First 15 days - ₹5/day, After 15 days - ₹50/day
FINE_FIRST_15_DAYS = 5.00  # Fine per day for first 15 days
FINE_AFTER_15_DAYS = 50.00  # Fine per day after 15 days
DEFAULT_LOAN_DAYS = 7
# Always use the DB file located next to this script, unless on Vercel
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/library.db"
else:
    DATABASE = os.path.join(os.path.dirname(__file__), 'library.db')

# -------------------- DATABASE CONNECTION --------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_zyYesiKh2V0L@ep-raspy-meadow-akbv2n5w-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    pass

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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        if request.method == "POST":
            title = request.form["title"].strip()
            author = request.form["author"].strip()
            total_copies = int(request.form.get("total_copies", 1))
            publish_year = request.form.get("publish_year")
            publish_year = int(publish_year) if publish_year else None
            # Prevent duplicate titles on different rows
            cursor.execute(
                "SELECT book_id FROM books_new WHERE LOWER(title) = LOWER(%s) AND book_id <> %s",
                (title, book_id)
            )
            conflict = cursor.fetchone()
            if conflict:
                flash("A book with this title already exists. Please update copies instead.", "danger")
                return redirect(url_for("edit_book", book_id=book_id))

            cursor.execute(
                "UPDATE books_new SET title=%s, author=%s, total_copies=%s, publish_year=%s WHERE book_id=%s",
                (title, author, total_copies, publish_year, book_id)
            )
            conn.commit()
            flash("Book updated.", "success")
            return redirect(url_for("books"))

        cursor.execute("SELECT * FROM books_new WHERE book_id=%s", (book_id,))
        book = cursor.fetchone()
        if not book:
            flash("Book not found.", "danger")
            return redirect(url_for("books"))
        return render_template("edit_book.html", book=book)
    except Exception as e:
        flash(f"Error updating book: {str(e)}", "danger")
        return redirect(url_for("books"))
    finally:
        conn.close()

@app.route("/books/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_book():
    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        total_copies = int(request.form.get("total_copies", 1))
        publish_year = request.form.get("publish_year")
        publish_year = int(publish_year) if publish_year else None
        if not title or not author:
            flash("Title and Author are required.", "danger")
            return redirect(url_for("add_book"))

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # If a book with the same title already exists, just increment copies
        cursor.execute("SELECT book_id, total_copies, available_copies FROM books_new WHERE LOWER(title) = LOWER(%s)", (title,))
        existing = cursor.fetchone()
        if existing:
            new_total = (existing.get("total_copies") or 0) + total_copies
            new_available = (existing.get("available_copies") or 0) + total_copies
            cursor.execute(
                "UPDATE books_new SET total_copies = %s, available_copies = %s, author = %s, publish_year = COALESCE(%s, publish_year) WHERE book_id = %s",
                (new_total, new_available, author, publish_year, existing["book_id"]) 
            )
        else:
            cursor.execute(
                "INSERT INTO books_new (title, author, total_copies, available_copies, publish_year) VALUES (%s, %s, %s, %s, %s)",
                (title, author, total_copies, total_copies, publish_year)
            )
        conn.commit()
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
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

        # Real-time totals based on current filters
        total_titles = len(books_list)
        total_copies = sum((b.get('total_copies') or 0) for b in books_list)

        return render_template(
            "books.html",
            books=books_list,
            q=q,
            available_filter=available_filter,
            total_titles=total_titles,
            total_copies=total_copies
        )
    except Exception as e:
        flash(f"Error loading books: {str(e)}", "danger")
        return render_template("books.html", books=[], q=q, available_filter=available_filter, total_titles=0, total_copies=0)
    finally:
        conn.close()

# -------------------- ISSUE BOOK --------------------
@app.route("/books/issue/<int:book_id>", methods=["GET", "POST"])
@login_required
@admin_required
def issue_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
        conn.close()

        flash("Book issued successfully!", "success")
        return redirect(url_for("transactions"))

    # Fetch all members for the dropdown
    cursor.execute("SELECT member_id, name FROM members ORDER BY name")
    members = cursor.fetchall()
    
    conn.close()
    return render_template("issue_book.html", book=book, members=members)

# -------------------- RETURN BOOK --------------------
@app.route("/books/return/<int:txn_id>", methods=["POST"])
@login_required
@admin_required
def return_book(txn_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute("SELECT * FROM transactions WHERE txn_id=%s", (txn_id,))
        txn = cursor.fetchone()
        if not txn or txn.get("status") != "issued":
            flash("Transaction invalid.", "warning")
            return redirect(url_for("transactions"))

        now = datetime.now()
        fine = 0.0
        if txn.get("due_date"):
            due_date = txn["due_date"]
            if isinstance(due_date, str):
                try:
                    due_date = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    due_date = datetime.fromisoformat(due_date)
            delta_days = (now.date() - due_date.date()).days
            if delta_days > 0:
                # Calculate fine with tiered structure
                if delta_days <= 15:
                    fine = round(delta_days * FINE_FIRST_15_DAYS, 2)
                else:
                    first_15_days_fine = 15 * FINE_FIRST_15_DAYS
                    remaining_days = delta_days - 15
                    additional_fine = remaining_days * FINE_AFTER_15_DAYS
                    fine = round(first_15_days_fine + additional_fine, 2)

        cursor.execute(
            "UPDATE transactions SET status='returned', return_date=%s, fine=%s WHERE txn_id=%s",
            (now, fine, txn_id)
        )
        cursor.execute(
            "UPDATE books_new SET available_copies = available_copies + 1 WHERE book_id=%s",
            (txn["book_id"],)
        )

        conn.commit()
        flash(f"Book returned. Fine: ₹{fine:.2f}" if fine > 0 else "Book returned successfully!", "success")
        return redirect(url_for("transactions"))
    except Exception as e:
        conn.rollback()
        flash(f"Error returning book: {str(e)}", "danger")
        return redirect(url_for("transactions"))
    finally:
        conn.close()

# -------------------- DELETE BOOK --------------------
@app.route("/books/delete/<int:book_id>", methods=["POST"])
@login_required
@admin_required
def delete_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Prevent deletion if there are any transactions for this book (keeps history intact)
    cursor.execute("SELECT COUNT(*) AS cnt FROM transactions WHERE book_id=%s", (book_id,))
    count_row = cursor.fetchone()
    has_references = (count_row.get("cnt") if isinstance(count_row, dict) else 0) or 0
    if has_references > 0:
        conn.close()
        flash("Cannot delete this book because transactions exist for it.", "warning")
        return redirect(url_for("books"))

    cursor.execute("DELETE FROM books_new WHERE book_id=%s", (book_id,))
    conn.commit()
    conn.close()
    flash("Book deleted.", "success")
    return redirect(url_for("books"))

# -------------------- TRANSACTIONS --------------------
@app.route('/transactions')
@login_required
def transactions():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
    conn.close()
    return render_template('transactions.html', transactions=transactions)

# -------------------- EXPORT CSV --------------------
@app.route("/transactions/export")
@login_required
@admin_required
def export_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
            r["issue_date"],
            r["due_date"],
            r["return_date"],
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # 1. Transaction Status Distribution (Pie Chart)
        cursor.execute("SELECT status, COUNT(*) AS count FROM transactions GROUP BY status")
        status_data = cursor.fetchall()
        pie_labels = [row["status"] for row in status_data]
        pie_values = [row["count"] for row in status_data]

        # 2. Top 5 Most Issued Books (Bar Chart)
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

        # 3. Monthly Transaction Trends (Line Chart)
        cursor.execute("""
            SELECT to_char(issue_date, 'YYYY-MM') as month, COUNT(*) as count
            FROM transactions
            WHERE issue_date >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY to_char(issue_date, 'YYYY-MM')
            ORDER BY month
        """)
        monthly_data = cursor.fetchall()
        line_labels = [row["month"] for row in monthly_data]
        line_values = [row["count"] for row in monthly_data]

        # 4. Overdue Books (Doughnut Chart)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN t.status = 'issued' AND t.due_date < CURRENT_DATE THEN 'Overdue'
                    WHEN t.status = 'issued' AND t.due_date >= CURRENT_DATE THEN 'On Time'
                    ELSE 'Returned'
                END as status,
                COUNT(*) as count
            FROM transactions t
            WHERE t.status = 'issued'
            GROUP BY 
                CASE 
                    WHEN t.status = 'issued' AND t.due_date < CURRENT_DATE THEN 'Overdue'
                    WHEN t.status = 'issued' AND t.due_date >= CURRENT_DATE THEN 'On Time'
                    ELSE 'Returned'
                END
        """)
        overdue_data = cursor.fetchall()
        overdue_labels = [row["status"] for row in overdue_data]
        overdue_values = [row["count"] for row in overdue_data]

        # 5. Member Activity (Horizontal Bar Chart)
        cursor.execute("""
            SELECT m.name, COUNT(t.txn_id) as activity_count
            FROM members m
            LEFT JOIN transactions t ON m.member_id = t.member_id
            GROUP BY m.member_id, m.name
            ORDER BY activity_count DESC
            LIMIT 10
        """)
        member_data = cursor.fetchall()
        member_labels = [row["name"] for row in member_data]
        member_values = [row["activity_count"] for row in member_data]

        # 6. Current Books Issued to Each Member
        cursor.execute("""
            SELECT m.name, COUNT(t.txn_id) as current_loans
            FROM members m
            LEFT JOIN transactions t ON m.member_id = t.member_id AND t.status = 'issued'
            GROUP BY m.member_id, m.name
            HAVING current_loans > 0
            ORDER BY current_loans DESC
        """)
        current_loans_data = cursor.fetchall()

        # 7. Recent Activities
        cursor.execute("""
            SELECT m.name AS member_name, b.title AS book_title, t.status, t.issue_date
            FROM transactions t
            JOIN members m ON t.member_id = m.member_id
            JOIN books_new b ON t.book_id = b.book_id
            ORDER BY t.issue_date DESC
            LIMIT 10
        """)
        recent_activities_data = cursor.fetchall()
        recent_activities = [
            f"{row['member_name']} {row['status']} '{row['book_title']}'"
            for row in recent_activities_data
        ]

        # 8. Statistics Cards
        cursor.execute("SELECT COUNT(*) as total_books FROM books_new")
        total_books = cursor.fetchone()["total_books"]
        
        cursor.execute("SELECT COUNT(*) as total_members FROM members")
        total_members = cursor.fetchone()["total_members"]
        
        cursor.execute("SELECT COUNT(*) as active_loans FROM transactions WHERE status = 'issued'")
        active_loans = cursor.fetchone()["active_loans"]
        
        cursor.execute("SELECT COUNT(*) as overdue_books FROM transactions WHERE status = 'issued' AND due_date < CURRENT_DATE")
        overdue_books = cursor.fetchone()["overdue_books"]

        return render_template(
            "dashboard.html",
            pie_labels=pie_labels,
            pie_values=pie_values,
            bar_labels=bar_labels,
            bar_values=bar_values,
            line_labels=line_labels,
            line_values=line_values,
            overdue_labels=overdue_labels,
            overdue_values=overdue_values,
            member_labels=member_labels,
            member_values=member_values,
            current_loans_data=current_loans_data,
            recent_activities=recent_activities,
            total_books=total_books,
            total_members=total_members,
            active_loans=active_loans,
            overdue_books=overdue_books
        )
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for("index"))
    finally:
        conn.close()

# -------------------- RUN --------------------
if __name__ == "__main__":
    # Initialize database
    init_db()
    print("🚀 Starting Library Management System with SQLite...")
    print("📚 Database initialized with sample data")
    print("🔐 Admin credentials: admin / admin123")
    print(f"🗄️ Using SQLite DB: {DATABASE}")
    print("🌐 Open: http://localhost:5000")
    app.run(debug=True)
