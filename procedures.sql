USE library_dbms;

DELIMITER //
CREATE PROCEDURE get_member_transactions(IN m_id INT)
BEGIN
    SELECT * FROM transactions WHERE member_id = m_id;
END;
//
DELIMITER ;
