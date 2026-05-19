# Library Management System - Project Report

## 📖 Project Overview
The Library Management System is a robust, production-ready web application designed to handle book inventory, member tracking, and book loan transactions. Originally built on SQLite, the system has been entirely upgraded to use a highly scalable **Neon PostgreSQL** database using connection pooling, making it completely ready for a serverless deployment on **Vercel**.

### Technology Stack
*   **Backend:** Python 3, Flask framework
*   **Database:** Neon PostgreSQL
*   **Database Driver:** `psycopg2-binary` (Using `ThreadedConnectionPool` for high concurrency)
*   **Frontend:** HTML5, Vanilla CSS3 (Custom Premium Design System), Jinja2 Templating
*   **Authentication:** `werkzeug.security` for password hashing, Flask Sessions
*   **Charts & Analytics:** Chart.js

---

## 🔐 User Roles & Authentication
The system uses session-based authentication to manage access control. There are two primary roles:

1.  **Admin** (Default username: `admin`): Has full CRUD (Create, Read, Update, Delete) privileges across the entire system. Can add/edit books, manage members, process returns, and view analytical dashboards.
2.  **Member**: A restricted view. Can browse the book catalog, search for books, and view their personal loan history.

**Buttons/Features:**
*   **Sign In:** Authenticates the user and redirects them to the Dashboard.
*   **Sign Up:** Allows new users to create a Member account (passwords are securely hashed).
*   **Logout:** Clears the user's session safely and redirects to the login screen.

---

## 🖥️ Core Modules & Features

### 1. Main Dashboard (`/`)
The landing page after authentication. It provides a quick glance at the current state of the library.
*   **Features:**
    *   **KPI Cards:** Displays total books, total members, active loans, and total fines.
    *   **Low Stock Alerts:** A warning banner alerting the Admin to books that are running out of available copies.
    *   **Recent Activity Feed:** A chronological list of the most recent transactions (who issued/returned what book and when).

### 2. Book Management (`/books`)
The central catalog for all books in the library.
*   **Features:**
    *   **Smart Search:** A case-insensitive search bar (using PostgreSQL `ILIKE`) that instantly filters books by Title or Author.
    *   **Dynamic Pagination:** Book lists are paginated to handle massive inventories gracefully.
    *   **Availability Tracking:** Automatically calculates how many copies are currently available vs. how many are out on loan.
*   **Buttons (Admin Only):**
    *   `+ Add New Book`: Opens a premium styled form to register a new book to the database.
    *   `Issue`: Opens the checkout form to assign the book to a specific member.
    *   `Edit`: Allows modifying the book's title, author, total copies, or publish year.
    *   `Delete`: Permanently removes a book from the catalog (requires confirmation).

### 3. Transaction Tracking (`/transactions`)
A comprehensive ledger of all book loans, returns, and financial penalties.
*   **Features:**
    *   **Status Indicators:** Color-coded badges indicating if a book is `issued` (yellow/red if overdue) or `returned` (green).
    *   **Fine Calculation Engine:** Automatically calculates overdue fines dynamically based on the current date vs. the expected return date. (₹5/day for the first 15 days, ₹50/day after).
*   **Buttons (Admin Only):**
    *   `Return Book`: Processes the return of an active loan, finalizes any pending fines, and increments the available book stock.
    *   `Search Transactions`: Filter historical transactions by book title or member name.

### 4. Member Management (`/members`) *[Admin Only]*
The directory of all registered library patrons.
*   **Features:**
    *   **Member Directory:** A searchable table of all library members, their contact info, and their join dates.
    *   **Active Loan Counter:** Shows exactly how many books a specific member currently has checked out.
*   **Buttons:**
    *   `+ Add New Member`: Register a new patron into the system.
    *   `Edit`: Modify a member's contact information.
    *   `Delete`: Remove a member from the system (blocked if they have active unreturned books).

### 5. Admin Analytics Dashboard (`/admin_dashboard`) *[Admin Only]*
A high-level statistical overview of the library's performance, powered by complex SQL aggregations.
*   **Features & Visualizations:**
    *   **Transaction Status Distribution:** A Pie chart showing the ratio of currently issued books vs. returned books.
    *   **Top 5 Most Issued Books:** A Bar chart highlighting the most popular books in the library.
    *   **Monthly Transaction Trends:** A Line graph tracking library activity over the last 12 months.
    *   **Member Activity Rankings:** A tabular ranking of the most active readers.
    *   **Current Books Issued to Members:** A real-time count of who holds the most library property.

---

## 🎨 Global UI/UX Features
*   **Responsive Sidebar Navigation:** A collapsible sidebar that automatically hides links the user is not authorized to see.
*   **Persistent Dark Mode / Light Mode Toggle:** A button located in the top-right header that allows users to instantly switch between a sleek dark theme and a clean light theme. The preference is saved in the browser's `localStorage` so it persists across sessions.
*   **Flash Messaging System:** Elegant toast-like notifications that pop up to inform the user of successes (e.g., "Book Returned Successfully") or errors (e.g., "Invalid Password").
*   **Intelligent Routing:** The system prevents authenticated users from accidentally navigating back to the login/signup pages by automatically redirecting them to their dashboard.

---

## ⚙️ Backend Architecture Highlights
*   **Threaded Connection Pooling:** Resolves Vercel's serverless cold-start and database latency issues by maintaining a pool of ready-to-use PostgreSQL connections (`psycopg2.pool.ThreadedConnectionPool`).
*   **Environment Variable Security:** Sensitive database credentials and secret keys are securely loaded via `.env` and `python-dotenv`, ensuring passwords are never hardcoded into the source code.
*   **Vercel Integration:** Configured via `api/index.py` and `vercel.json` to route all incoming HTTP traffic through the standard Flask application instance.
