"""Extract the ticket desk's MYSQL tables into files for our data warehouse"""

import csv
import json
from os import read
from pathlib import Path

from db import connect

EXPORTS = Path("exports") # this will be a directory to hold table csvs
TABLES = ("priorities", "customers", "agents", "tickets")

def read_table(conn, table):
    """Return every row of a given table in our db as a list of dictionaries"""
    cursor = conn.cursor(dictionary=True) # Rather than manually wrangling stuff into dict, output as dict
    cursor.execute(f"SELECT * FROM {table}") # Use an f-string because a table name can't be a parameter


    rows = cursor.fetchall() # rows is what holds our dictionaries (in an outer list)

    cursor.close()
    conn.commit() # Ends the underlying transaction that the connection creates

    return rows

def write_csv(rows, path):
    """Write rows to a csv file, with a header row containing column names"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        # Let's write the csv's
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader() # Writing the header row 
        writer.writerows(rows)

def write_jsonL(rows, path):
    """Write rows to a json-lines file, one JSON-L object per line"""
    with open (path, "w", newline="", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str)+ "\n")

def main():
    """Export our four tables into CSV files, and the event history to JSON-lines"""
    EXPORTS.mkdir(exist_ok=True) # if the folder exists, just continue without exception (no over-write)
    conn = connect()

    for table in TABLES:
        rows = read_table(conn, table)
        write_csv(rows, EXPORTS / f"{table}.csv")
        print(table, len(rows))

    #write ticket events to JSON-L
    events = read_table(conn, "ticket_events")
    write_jsonL(events, EXPORTS /"ticket_events.jsonl")
    print("ticket_events", len(events))
    conn.close()


if __name__ == "__main__":
    main()
