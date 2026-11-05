--how long does a ticket tacke to close per priority?
-- A priority whose average passes the SLA where the desk staffs first
SELECT t.priority, t.sla_hours, AVG(f.hours_since_open) as hours_to_close, SUM(f.event_count) AS closed,
    CASE
    WHEN AVG(f.hours_since_open) <= t.sla_hours THEN 'within SLA'
    ELSE 'over SLA' END AS sla_band
FROM desk_dw.fact_ticket_events as f
JOIN desk_dw.dim_ticket as t on t.ticket_key = f.ticket_key
WHERE f.kind = 'closed'
GROUP BY t.priority, t.sla_hours
ORDER BY t.priority;

-- which weekdays and agents see the most ticket events 
-- The busiest weekday per agent is where a second agent helps
SELECT d.weekday, d.is_weekend, a.name as agent, SUM(f.event_count) as events
FROM desk_dw.fact_ticket_events as f
JOIN desk_dw.dim_date as d ON d.date_key = f.date_key
JOIN desk_dw.dim_agent as a ON a.agent_key = f.agent_key
GROUP BY  d.weekday, d.is_weekend, a.name
ORDER BY d.weekday, agent;

-- whose tickets moved on one day?
-- one day's movers are the customers the desk calls back first
SELECT c.name as customer, SUM(event_count) AS events
FROM desk_dw.fact_ticket_events as f
JOIN desk_dw.dim_customer as c on c.customer_key = f.customer_key
WHERE  f.event_date ='2026-10-18'
GROUP BY c.name
ORDER BY  events DESC, customer;