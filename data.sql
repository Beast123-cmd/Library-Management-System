USE library_dbms;

-- Create one admin for login
INSERT INTO users (username, password, role)
VALUES ('admin', '$2b$12$QjIgoZ5q2S6sLhHsvd1qLeuSh8j7ZbX2X5E9TwvJxgVyzD2KQw8bS', 'admin');
-- password = "admin123"

-- Sample members
INSERT INTO members (name, email) VALUES ('John Doe', 'john@example.com');
INSERT INTO members (name, email) VALUES ('Jane Smith', 'jane@example.com');

-- Sample books
INSERT INTO books (title, author) VALUES ('DBMS Concepts', 'Elmasri & Navathe');
INSERT INTO books (title, author) VALUES ('Operating Systems', 'Galvin');
