#!/usr/bin/env python3
"""
Database setup script for Library Management System.
This script will help you set up the MySQL database and user.
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

def create_database_and_user():
    """Create the database and user for the library management system."""
    
    print("🔧 Setting up Library Management System Database...")
    print("=" * 60)
    
    # Get MySQL root credentials
    print("📝 Please provide your MySQL root credentials:")
    root_user = input("MySQL root username [root]: ").strip() or "root"
    root_password = input("MySQL root password: ").strip()
    
    if not root_password:
        print("❌ Root password is required!")
        return False
    
    try:
        # Connect as root
        print("\n🔌 Connecting to MySQL as root...")
        connection = mysql.connector.connect(
            host='localhost',
            user=root_user,
            password=root_password
        )
        
        if connection.is_connected():
            print("✅ Connected to MySQL successfully!")
            cursor = connection.cursor()
            
            # Create database
            print("\n📚 Creating database 'library_dbms'...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS library_dbms")
            print("✅ Database 'library_dbms' created successfully!")
            
            # Create user
            print("\n👤 Creating user 'library_admin'...")
            try:
                cursor.execute("CREATE USER IF NOT EXISTS 'library_admin'@'localhost' IDENTIFIED BY 'libpass123'")
                print("✅ User 'library_admin' created successfully!")
            except Error as e:
                if "already exists" in str(e):
                    print("ℹ️  User 'library_admin' already exists, updating password...")
                    cursor.execute("ALTER USER 'library_admin'@'localhost' IDENTIFIED BY 'libpass123'")
                    print("✅ User password updated successfully!")
                else:
                    raise e
            
            # Grant privileges
            print("\n🔑 Granting privileges to 'library_admin'...")
            cursor.execute("GRANT ALL PRIVILEGES ON library_dbms.* TO 'library_admin'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print("✅ Privileges granted successfully!")
            
            # Close root connection
            cursor.close()
            connection.close()
            
            # Test new user connection
            print("\n🧪 Testing connection with 'library_admin'...")
            test_connection = mysql.connector.connect(
                host='localhost',
                user='library_admin',
                password='libpass123',
                database='library_dbms'
            )
            
            if test_connection.is_connected():
                print("✅ Connection test successful!")
                test_connection.close()
                return True
            else:
                print("❌ Connection test failed!")
                return False
                
    except Error as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_tables():
    """Create the database tables."""
    
    print("\n📋 Creating database tables...")
    
    try:
        # Connect with library_admin
        connection = mysql.connector.connect(
            host='localhost',
            user='library_admin',
            password='libpass123',
            database='library_dbms'
        )
        
        cursor = connection.cursor()
        
        # Read and execute schema.sql
        schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_file):
            print("📖 Reading schema.sql...")
            with open(schema_file, 'r') as file:
                schema_sql = file.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            print("✅ Database tables created successfully!")
        else:
            print("⚠️  schema.sql not found, creating basic tables...")
            create_basic_tables(cursor)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Table creation failed: {e}")
        return False

def create_basic_tables(cursor):
    """Create basic tables if schema.sql is not available."""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'member') DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Members table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books_new (
            book_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            total_copies INT DEFAULT 1,
            available_copies INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id INT AUTO_INCREMENT PRIMARY KEY,
            member_id INT NOT NULL,
            book_id INT NOT NULL,
            issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            return_date TIMESTAMP NULL,
            status ENUM('issued', 'returned') DEFAULT 'issued',
            fine DECIMAL(10,2) DEFAULT 0.00,
            FOREIGN KEY (member_id) REFERENCES members(member_id),
            FOREIGN KEY (book_id) REFERENCES books_new(book_id)
        )
    """)
    
    print("✅ Basic tables created successfully!")

def insert_sample_data():
    """Insert sample data into the database."""
    
    print("\n📊 Inserting sample data...")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='library_admin',
            password='libpass123',
            database='library_dbms'
        )
        
        cursor = connection.cursor()
        
        # Insert admin user
        from werkzeug.security import generate_password_hash
        admin_password = generate_password_hash('admin123')
        
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, role) 
            VALUES ('admin', %s, 'admin')
        """, (admin_password,))
        
        # Insert sample member
        cursor.execute("""
            INSERT IGNORE INTO members (name, email) 
            VALUES ('John Doe', 'john@example.com')
        """)
        
        # Insert sample books
        sample_books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', 3, 3),
            ('To Kill a Mockingbird', 'Harper Lee', 2, 2),
            ('1984', 'George Orwell', 4, 4),
            ('Pride and Prejudice', 'Jane Austen', 2, 2),
            ('The Catcher in the Rye', 'J.D. Salinger', 1, 1)
        ]
        
        for title, author, total, available in sample_books:
            cursor.execute("""
                INSERT IGNORE INTO books_new (title, author, total_copies, available_copies) 
                VALUES (%s, %s, %s, %s)
            """, (title, author, total, available))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Sample data inserted successfully!")
        print("\n🔐 Default Admin Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        
        return True
        
    except Error as e:
        print(f"❌ Sample data insertion failed: {e}")
        return False

def main():
    """Main setup function."""
    
    print("🚀 Library Management System - Database Setup")
    print("=" * 60)
    
    # Step 1: Create database and user
    if not create_database_and_user():
        print("\n❌ Database setup failed!")
        return False
    
    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Table creation failed!")
        return False
    
    # Step 3: Insert sample data
    if not insert_sample_data():
        print("\n❌ Sample data insertion failed!")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Run the application: python app.py")
    print("   2. Open your browser: http://localhost:5000")
    print("   3. Login with admin credentials: admin / admin123")
    print("\n✨ Your Library Management System is ready to use!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
