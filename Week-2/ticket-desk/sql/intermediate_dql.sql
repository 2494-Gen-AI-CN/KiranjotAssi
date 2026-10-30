-- Active: 1793208308507@@127.0.0.1@3306@ticket_desk
SELECT ticket_id, title, priority, status 
FROM tickets 
WHERE priority = 'high' AND status <> 'closed'; -- priority high, status NOT EQUAL to 'closed'


SELECT ticket_id, title, status 
FROM tickets
WHERE status IN ('open', 'assigned'); -- saves us chaining with or when checking same column

SELECT * FROM tickets   
WHERE opened_at 
BETWEEN '2026-10-18 00:00:00' AND '2026-10-18 23:59:59';

--STRING SEARCHING 
SELECT ticket_id, title FROM tickets
WHERE title LIKE '%page%';

--USE IS AND IS NOT FOR NULL/NOT NULL CHECKS
SELECT ticket_id, title FROM tickets
WHERE agent_id IS NULL;

SELECT ticket_id , title, opened_at FROM tickets
ORDER BY opened_at DESC
LIMIT 3;

-- COLUMN ALIASING & SCALAR FUNCTIONS
SELECT UPPER(name) FROM agents;

-- CONCAT + ALIAS
SELECT CONCAT('TD - ', ticket_id) AS ref, title 
FROM tickets AS t;

SELECT ticket_id, round(TIMESTAMPDIFF(MINUTE, opened_at, closed_at)/60, 1) AS hours 
FROM tickets
ORDER BY hours DESC;

-- aggregate functions
SELECT COUNT(*) AS tickets
FROM tickets;

-- group by and having
SELECT status, COUNT(*) AS tickets 
FROM tickets
GROUP BY status;

SELECT priority, ROUND(AVG(TIMESTAMPDIFF(MINUTE, opened_at, closed_at)/60), 1) AS avg_hours
FROM tickets
GROUP BY priority
HAVING AVG(TIMESTAMPDIFF(MINUTE, opened_at, closed_at)/60) > 5;

-- subqueries
-- nesting queries inside of other queries
--SQL database engine runs the inner query, then the outer query against the result set of the inner query
SELECT ticket_id, title FROM tickets
WHERE customer_id = (SELECT customer_id FROM  customers WHERE email = 'jonathan.delacruz@revature.com');

--IF THE INNER QUERY RETURNS MORE THAN ONE VALUE, USE IN INSTEAD OF EQUALS
SELECT ticket_id, title FROM tickets
WHERE  customer_id IN (SELECT customer_id FROM customers WHERE country = 'US');

-- A SUBQUERY ONLY RETURNS INFO FROM ONE TABLE IN ITS RESULTS SET, 
-- EVEN IF IT LOOKS INTO ANOTHER TABLE TO DO SOME FILTRATION BASED ON A COMPARISON
-- IF WE NEED VALUES FROM TWO TABLES IN THE SAME RESULT SET - WE NEED A JOIN
SELECT t.ticket_id, t.title, c.name AS customer
FROM tickets AS t 
INNER JOIN customers AS c 
ON c.customer_id = t.customer_id;
-- This is an equi join (strict equals)

--theta join uses an ON condition that's anything other than equality
SELECT t.ticket_id, t.title, p.sla_hours, TIMESTAMPDIFF(HOUR, t.opened_at, t.closed_at) AS hours 
FROM tickets AS t
JOIN priorities AS p
ON p.priority = t.priority 
AND TIMESTAMPDIFF(HOUR, t.opened_at, t.closed_at)  > p.sla_hours;

-- left join keeps entire left table, right join is inverse, keeps every row of the right table
SELECT  a.name, t.ticket_id from agents as a
LEFT JOIN tickets as t on t.agent_id = a.agent_id;

--complex multi-joins
SELECT t.ticket_id, t.title, t.priority, t.status, c.name, a.name, DATE_ADD(t.opened_at, INTERVAL p.sla_hours HOUR) AS deadline 
FROM  tickets AS t
JOIN customers AS c on c.customer_id = t.customer_id
JOIN priorities as p on p.priority = t.priority
LEFT JOIN agents as a on a.agent_id = t.agent_id
ORDER BY t.ticket_id;


-- MYSQL doesn't have a full outer join
--if we want that, we have to use a left join, union, right join
--UNION combines the result sets of two or more result sets, into one single distinct result set
--automatically removes duplicate rows
SELECT a.name, t.ticket_id
FROM agents AS a
LEFT JOIN tickets as t
on t.agent_id = a.agent_id
UNION
SELECT a.name, t.ticket_id
from agents as a
RIGHT JOIN tickets as t 
on t.agent_id=a.agent_id

SELECT a.name as agent, p.priority 
from agents as a
CROSS JOIN priorities as p
ORDER BY a.agent_id, p.sla_hours;