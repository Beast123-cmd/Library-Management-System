USE library_dbms;

-- When a book is issued, set available = FALSE
DELIMITER //
CREATE TRIGGER issue_book_trigger
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    UPDATE books SET available = FALSE WHERE book_id = NEW.book_id;
END;
//
DELIMITER ;

-- When a book is returned, set available = TRUE
DELIMITER //
CREATE TRIGGER return_book_trigger
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF NEW.status = 'returned' THEN
        UPDATE books SET available = TRUE WHERE book_id = NEW.book_id;
    END IF;
END;
//
DELIMITER ;
