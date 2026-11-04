bq load --replace --source_format=CSV --skip_leading_rows=1 desk_raw.priorities exports/priorities.csv priority:STRING,sla_hours:INTEGER

bq load --replace --source_format=CSV --skip_leading_rows=1 desk_raw.customers exports/customers.csv customer_id:INTEGER,name:STRING,email:STRING,country:STRING,monthly_fee:NUMERIC

bq load --replace --source_format=CSV --skip_leading_rows=1 desk_raw.agents exports/agents.csv agent_id:INTEGER,name:STRING,email:STRING

bq load --replace --source_format=CSV --skip_leading_rows=1 desk_raw.tickets exports/tickets.csv ticket_id:INTEGER,title:STRING,priority:STRING,status:STRING,customer_id:INTEGER,agent_id:INTEGER,opened_at:DATETIME,closed_at:DATETIME

bq load --replace --source_format=NEWLINE_DELIMITED_JSON desk_raw.ticket_events exports/ticket_events.jsonl warehouse/schemas/ticket_events.json




