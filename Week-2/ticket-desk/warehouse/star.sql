-- One row per day, from the desk's first ticket to 90 days after its last event
CREATE OR REPLACE TABLE desk_dw.dim_date AS
WITH span AS(
    SELECT 
        (SELECT DATE(MIN(opened_at)) FROM desk_raw.tickets) AS first_day,
        (SELECT DATE_ADD(DATE(MAX(created_at)), INTERVAL 90 DAY) FROM desk_raw.ticket_events) AS last_day
)
SELECT
    CAST(FORMAT_DATE('%Y%m%d', day) AS INT64) AS date_key,
    day AS full_date,
    EXTRACT(YEAR FROM day) AS year,
    EXTRACT(MONTH FROM day) AS month,
    FORMAT_DATE('%A', day) AS weekday,
    EXTRACT(DAYOFWEEK FROM day) IN (1,7)AS is_weekend
FROM span, UNNEST(GENERATE_DATE_ARRAY(span.first_day, span.last_day)) AS day;

--one row per agent, plus key 0 for a ticket nobody holds
CREATE OR REPLACE TABLE desk_dw.dim_agent AS
SELECT
    agent_id AS agent_key,
    agent_id,
    name,
    email
FROM desk_raw.agents
UNION ALL
SELECT 
    0, 
    NULL,
    'unassigned',
    NULL;

-- THE CUSTOMERS, EACH ROW WITH A KEY IN THE WAREHOUSE
CREATE OR REPLACE TABLE  desk_dw.dim_customer AS
SELECT
    ROW_NUMBER() OVER (ORDER BY customer_id) AS customer_key,
    customer_id,
    name, 
    email,
    country,
    monthly_fee
FROM desk_raw.customers;

-- one row per priority, will be snowflake schma;s extra table
CREATE OR REPLACE TABLE desk_dw.dim_priority AS
SELECT
    priority, sla_hours
FROM desk_raw.priorities;
 --one row per ticket, with its prioirty folded in
CREATE OR REPLACE TABLE desk_dw.dim_ticket AS
SELECT
    t.ticket_id AS ticket_key,
    t.ticket_id,
    t.title,
    t.priority,
    p.sla_hours,
    t.status,
    t.opened_at,
    t.closed_at
FROM desk_raw.tickets AS t
JOIN desk_raw.priorities AS p
    ON p.priority = t.priority;

--the fact: each event with its keys are split by day
CREATE OR REPLACE TABLE desk_dw.fact_ticket_events
PARTITION BY event_date
CLUSTER BY  ticket_key
AS
SELECT
    e.event_id,
    t.ticket_id as ticket_key, 
    c.customer_key,
    COALESCE(t.agent_id, 0) AS agent_key,
    CAST(FORMAT_DATE('%Y%m%d', DATE(e.created_at)) AS INT64) AS date_key,
    DATE(e.created_at) as event_date,
    e.kind, 
    ROUND(DATETIME_DIFF(e.created_at, t.opened_at, MINUTE) / 60, 2) AS hours_since_open,
    1 AS event_count
FROM desk_raw.ticket_events AS e
JOIN desk_raw.tickets AS t ON t.ticket_id = e.ticket_id
JOIN desk_dw.dim_customer AS c ON c.customer_id = t.customer_id
WHERE e.kind IN ('open', 'assigned', 'closed')
AND e.created_at >= t.opened_at
QUALIFY ROW_NUMBER() OVER (PARTITION BY e.ticket_id, e.kind, e.created_at ORDER BY  e.event_id) = 1;