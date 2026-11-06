import pandas as pd
from google.cloud import bigquery
from src.config import PROJECT_ID, DATASET_ID


df = pd.read_parquet("data/leaderboard.parquet")
df["ingested_at"] = pd.Timestamp.now(tz="UTC")

client = bigquery.Client(project="rev-project0")
table_id = f"{PROJECT_ID}.{DATASET_ID}.leaderboard_snapshots"

job = client.load_table_from_dataframe(
    df,
    table_id,
    job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    ),
)
job.result()

print(f"Loaded {len(df)} rows into{table_id}")

