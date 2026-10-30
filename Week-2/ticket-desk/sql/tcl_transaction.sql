-- transaction control language

-- if we want to send money from one account at a bank to another 
--that sounds simple in english

-- in practice, that is a series of discreet steps

USE ticket_desk;

-- TCL we are wrapping individual statements inside a transaction
START TRANSACTION; -- DENOTES THE BEGINNING OF A TRANSACTION    
DELETE * FROM tickets;
ROLLBACK;  --typically used inside of a conditional check, or an exception try-catch
 -- it rolls everything back to the START TRANSACTION

 -- real transactions are typiclaly more complex
 START TRANSACTION;
 UPDATE tickets SET priority = 'normal' WHERE ticket_id = 6;
 SAVEPOINT before_title; -- a named marker inside a transaction

 UPDATE tickets SET title = 'Dark mode' WHERE ticket_id = 6;
 ROLLBACK TO SAVEPOINT before_title;
 COMMIT; -- commit saved everything in the transaction up to this point and ends it 

 -- ACID properties 
 -- atomicity: transactions are all or nothing,. If a single statement in the transactions fails, the entire transaction is rolled back to its original state (or a named savepoint)

 --consistency : there should never be invalid data as a result of a transaction. the database must transition from one valid state to another, following all schemas, constraints, tiggers

 --isolation - concurrent transactions execute independently from one another - wihtout interfering with reading or uncommitted data from one another. 

-- durability -