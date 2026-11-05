"""Reach the desk's BigQuery warehouse from Python."""
import os
from datetime import date
from decimal import Decimal
from google.cloud import bigquery

def client():
    """Return a BigQuery client for the project in DESK_GCP_PROJECT."""
    return bigquery.Client(project=os.environ["DESK_GCP_PROJECT"])

def run_sql_file(bq, path):
    """Run every statement of one SQL file as a single script."""
    with open(path, encoding="utf-8") as f:
        bq.query(f.read()).result()

def query_rows(bq, sql):
    """Return the rows of a query as a list of dicts."""
    return [dict(row) for row in bq.query(sql).result()]

def query_frame(bq, sql):
    """Return the rows of a query as a pandas DataFrame."""
    return bq.query(sql).to_dataframe()

def jsonable(row):
    """Return a copy of a row with its dates and decimals written as text."""
    return {key: str(value) if isinstance(value, (date, Decimal)) else value
            for key, value in row.items()}

def load_rows(bq, rows, table, mode="WRITE_TRUNCATE"):
    """Load rows into an existing table with that table's own schema."""
    config = bigquery.LoadJobConfig(schema=bq.get_table(table).schema, write_disposition=mode)
    job = bq.load_table_from_json([jsonable(row) for row in rows], table, job_config=config)
    job.result()
    return job.output_rows