"""Run the desk's ETL job: extract, stage, clean/transform, keep history, rebuild the star schema, log"""
from datetime import date, datetime, timezone
from db import connect
from dw import client, load_file, load_frame, load_rows, query_frame, query_rows, run_sql_file
from extract import EXPORTS, TABLES, read_events, read_table, write_csv, write_jsonl
from transform import apply_scd2, clean_events

def watermark(bq):
    """Returns the highest event_id already staged , or 0 when nothing is staged"""
    sql = "SELECT COALESCE(MAX(event_id), 0) as last FROM desk_raw.ticket_events"
    return query_rows(bq, sql)[0]["last"]

def run (conn, bq, as_of):
    """Run every ste of the job once and return the row it adds to the load log"""

    # Setup -> make sure dw has the tables, fine to repeat
    run_sql_file(bq, "warehouse/etl_tables.sql")
    EXPORTS.mkdir(exist_ok=True)

    # EXTRACT + STAGE (the four small tables): MySql -> SQL -> desk_raw, replaced completely every time
    for table in TABLES:
        path = EXPORTS /f"{table}".csv
        write_csv(read_table(conn, table), path)
        load_file(bq, path, f"desk_raw.{table}")

    #EXTRACT + STAGE (events,incremental )
    events = read_events(conn, watermark(bq)) # EXTRACTS new events only
    if events:
        write_jsonl(events, EXPORTS / "ticket_events.jsonl")
        load_file(bq, EXPORTS / "ticket_events.jsonl", "desk_raw.ticket_events", "WRITE_APPEND")

    #TRANSFORM (ETL) -> Cleaning events
    staged = query_frame(bq, "SELECT * FROM desk_raw.ticket_events")
    tickets = query_frame(bq, "SELECT ticket_id, opened_at FROM  desk_raq.tickets")
    clean, rejects = clean_events(staged, tickets)

    #LOAD
    load_frame(bq, clean, "desk_raw.ticket_events_clean")
    load_frame(bq, rejects, "desk_dw.load_rejects")

    # TRANSFORM (ETL) + LOAD: customer history
    dim = query_rows(bq, "SELECT * FROM desk_dw.dim_customer")
    src = query_rows(bq, "SELECT * FROM desk_raw.customers")

    load_rows(bq, apply_scd2(dim, src, as_of), "desk_dw.dim_customer")

    # LOAD + TRANSFORM (ELT): -> after the data has been loaded trasnform with star.sql
    run_sql_file(bq, "warehouse/star.sql")

    #LOG: one row per run, appended
    log = {
        "run_at_time": datetime.now(timezone.utc),
        "rows_read": len(events), 
        "rows_loaded": len(clean),
        "rows_rejected": len(rejects)
    }

    load_rows(bq, [log], "desk_dw.load_log", 'WRITE_APPEND')
    return log


def main():
    """Run the job once againts mysql and bigquery, and print the load log row"""
    conn = connect()
    print(run(conn, client(), date.today()))

    conn.close()

if __name__ == "__main__":
    main()