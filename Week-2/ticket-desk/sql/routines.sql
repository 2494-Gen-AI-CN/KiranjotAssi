-- Active: 1793208308507@@127.0.0.1@3306@ticket_desk
--Trigger - functions/ code that the server runs when a specific event (INSERT, UPDATE, DELETE) occurs on a specific table

DELIMITER //
CREATE TRIGGER tickets_status_change
AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status OR NOT (OLD.agent_id <=> NEW.agent_id) THEN
    INSERT INTO  ticket_events (ticket_id, kind, note)
    VALUES(NEW.ticket_id, NEW.status, CONCAT('Was ', OLD.status, ' agent', COALESCE(NEW.agent_id, 'none')));
    END IF;
END //
DELIMITER;

UPDATE tickets
SET status = 'closed', closed_at = CURRENT_TIMESTAMP
WHERE ticket_id = 5
SHOW TRIGGERS\G


--Views 

CREATE VIEW open_board AS
    SELECT t.ticket_id, t.title, t.priority, t.status, 
    c.name as customer_name, 
    a.name as agent_name, 
    DATE_ADD(t.opened_at, INTERVAL p.sla_hours HOUR) AS deadline 
    FROM  tickets AS t
    JOIN customers AS c on c.customer_id = t.customer_id
    JOIN priorities as p on p.priority = t.priority
    LEFT JOIN agents as a on a.agent_id = t.agent_id
    WHERE t.status <> 'closed'
    ORDER BY t.ticket_id;

SELECT * FROM open_board;

-- Stored Procedures
-- just a block of names SQL, similar to a tigger
-- can run it using CALL
-- user defined function ( returns a value). this doesn't have to return anything
DELIMITER //
CREATE PROCEDURE log_event(IN p_ticket_id INT, in p_kind VARCHAR(20), IN p_note VARCHAR(255))
BEGIN
    INSERT INTO ticket_events(ticket_id, kind, note)
    VALUES(p_ticket_id, p_kind, p_note);
END //

CREATE PROCEDURE close_ticket(IN p_ticket_id INT, IN p_closed_at DATETIME)
BEGIN
    UPDATE tickets
    SET status = 'closed', closed_at = p_closed_at
    WHERE ticket_id = p_ticket_id;
END
DELIMITER;

CALL log_event(1, 'test', 'Trying out my new stored procedure');

SELECT * FROM ticket_events;

CALL close_ticket(4, CURRENT_TIMESTAMP);

SELECT * FROM tickets;
select * from ticket_events;

-- User Defined Functions
CREATE FUNCTION hours_open(p_opened DATETIME, p_closed DATETIME)
RETURNS DECIMAL(8,2)
DETERMINISTIC
RETURN ROUND(TIMESTAMPDIFF(MINUTE, p_opened, p_closed)/ 60, 2);

SELECT ticket_id, hours_open(opened_at, closed_at) AS hours FROM tickets;

--Index
-- If we find ourselves commonly doing a lookup against a particular column's value - we can create an index
-- The databse engine stores everything in a B-tree

EXPLAIN SELECT * FROM tickets WHERE status = 'open';

CREATE INDEX idx_tickets_status ON tickets (status);

EXPLAIN SELECT * FROM tickets WHERE status = 'open';