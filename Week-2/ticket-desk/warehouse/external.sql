-- the agent's teams read from google sheets where they live
CREATE OR REPLACE EXTERNAL TABLE desk_raw.agent_teams(
    name string, 
    team string,
)
OPTIONS (
    format = 'GOOGLE_SHEETS',
    uris = ['https://docs.google.com/spreadsheets/d/1TaeNHvSyc5_Z_XzBcsj8oeMFo-9cHPvneIvifIdrUTY'],
    skip_leading_rows=1
)

--events per team 
SELECT s.team, SUM(f.event_count) as events
FROM desk_dw.fact_ticket_agent as f
JOIN desk_dw.dim_agent as a on a.agent_key =f.agent_key
JOIN desk_raw.agent_teams as s on s.name=a.name
GROUP BY s.team
ORDER BY s.team;