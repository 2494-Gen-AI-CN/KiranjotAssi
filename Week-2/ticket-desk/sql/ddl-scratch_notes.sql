USE ticket_desk; -- added to the top so MYSQL knows what dataabase to tagret


CREATE TABLE scratch_notes_(
    note_id INT, 
    body VARCHAR(255)
);

--alter lets us change someonething about a table that already exists. adding/dropping columns
--add new rules/constraints
ALTER TABLE scratch_notes ADD COLUMN author VARCHAR(50);

-- modify is used with author to change a tables definition
ALTER TABLE scratch_notes MODIFY body VARCHAR(500);

-- renames a column in place wihtout touching the definition
ALTER TABLE scratch_notes RENAME COLUMN author TO written_by;

-- drop table removes the whole table and everyhting inside it 
-- there is no undo, once it's gone, it's gone
ALTER TABLE scratch_notes DROP COLUMN wriiten_by;

-- insert rows
INSERT INTO scratch_notes (note_id, body) 
VALUES 
    (1, "This is my first note"),
    (2, "This is my second note");

-- very basic select
SELECT * FROM scratch_notes;

--truncate (empties all records from the table, but keeps the structure)
TRUNCATE TABLE scratch_notes;
SELECT * FROM scratch_notes; -- we should get nothing back here, but the table exists so no error

SHOW TABLES; 

DROP TABLE scratch_notes; --there is no going back
SHOW TABLES;