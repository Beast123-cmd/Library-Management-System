# 🚀 Library Management System - Setup Guide

## 🎯 Quick Start (Recommended - SQLite Version)

The easiest way to get started is with the SQLite version, which doesn't require MySQL setup:

### 1. Run the SQLite Version
```bash
cd "/Users/aayushangal/Documents/Library management project/library_management_system"
python app_sqlite.py
```

### 2. Access the Application
- Open your browser and go to: `http://localhost:5000`
- Login with admin credentials:
  - **Username**: `admin`
  - **Password**: `admin123`

### 3. That's it! 🎉
The SQLite version automatically creates the database and sample data for you.

---

## 🐬 MySQL Version (Advanced Setup)

If you prefer to use MySQL, follow these steps:

### 1. Set up MySQL Database
```bash
# Run the database setup script
python setup_database.py
```

This script will:
- Create the `library_dbms` database
- Create the `library_admin` user with password `libpass123`
- Set up all required tables
- Insert sample data

### 2. Run the MySQL Version
```bash
python app.py
```

### 3. Access the Application
- Open your browser and go to: `http://localhost:5000`
- Login with admin credentials:
  - **Username**: `admin`
  - **Password**: `admin123`

---

## 🔧 Troubleshooting

### MySQL Connection Issues
If you get MySQL connection errors:

1. **Check if MySQL is running**:
   ```bash
   # On macOS with Homebrew
   brew services start mysql
   
   # Or check if it's running
   brew services list | grep mysql
   ```

2. **Reset MySQL password** (if needed):
   ```bash
   mysql -u root -p
   # Then run: ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';
   ```

3. **Use the SQLite version instead** (recommended for testing):
   ```bash
   python app_sqlite.py
   ```

### Port Already in Use
If port 5000 is already in use:
```bash
# Kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or run on a different port
python app_sqlite.py --port 5001
```

### Permission Issues
If you get permission errors:
```bash
# Make sure you're in the correct directory
cd "/Users/aayushangal/Documents/Library management project/library_management_system"

# Check file permissions
ls -la app_sqlite.py
```

---

## 📱 Features Available

### 👤 User Roles
- **Admin**: Full access to all features
- **Member**: Can browse books and manage their transactions

### 📚 Book Management
- Browse the book catalog
- Search by title or author
- Filter by availability
- Issue and return books (members)
- Add/edit books (admin)

### 📊 Admin Dashboard
- View transaction statistics
- See popular books
- Export transaction data
- Monitor recent activities

### 🎨 Modern UI Features
- Responsive design (works on mobile/tablet/desktop)
- Dark mode toggle
- Smooth animations
- Modern, professional appearance

---

## 🔐 Default Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

### Sample Member Account
You can create new member accounts through the signup page.

---

## 📁 File Structure

```
library_management_system/
├── app.py              # MySQL version
├── app_sqlite.py       # SQLite version (recommended)
├── setup_database.py   # MySQL setup script
├── static/
│   ├── style.css       # Enhanced stylesheet
│   └── script.js       # Enhanced JavaScript
├── templates/          # HTML templates
└── library.db          # SQLite database (created automatically)
```

---

## 🆘 Need Help?

1. **Try the SQLite version first** - it's the easiest to set up
2. **Check the console output** for any error messages
3. **Make sure all dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Check if the port is available** (5000)

---

## 🎉 Enjoy Your Library Management System!

The application is now ready with:
- ✅ Modern, responsive UI
- ✅ Dark mode support
- ✅ Smooth animations
- ✅ Mobile-friendly design
- ✅ All buttons visible and functional
- ✅ Professional appearance

Happy managing! 📚✨
