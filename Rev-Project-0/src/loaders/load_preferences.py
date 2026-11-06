from datetime import datetime, timezone

import pandas as pd
from datasets import load_dataset
from google.cloud import bigquery
from src.config import PROJECT_ID, DATASET_ID

RELEASES = {
    "100k_2024": "lmarena-ai/arena-human-preference-100k",
    "140k_2025": "lmarena-ai/arena-human-preference-140k",
}

def first_present(row, names):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return None

def normalize_timestamp(value):
    if value is None:
        return None
    #The 100k release uses UNIX timestamps, 140k have timestamp strings
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return pd.to_datetime(value, utc=True, errors="coerce")

rows= []

for release, repo_id in RELEASES.items():
    dataset = load_dataset(repo_id, split="train", streaming=True)

    for row in dataset:
        rows.append({
            "release": release,
            "source-dataset": repo_id,
            "vote_timestamp": normalize_timestamp(
                first_present(row, ["timestamp", "tstamp"])
            ),
            "model_a": first_present(row,["model_a"]),
            "model_b": first_present(row, ["model_b"]),
            "winner_raw": first_present(row, ["winner", "actual_score"]),
            "language": first_present(row, ["language", "language_tag"])
        })
df= pd.DataFrame(rows)

client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET_ID}.preference_votes"

job = client.load_table_from_dataframe(
    df,
    table_id,
    job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    ),
)
job.result()

print(f"Loaded {len(df)} rows into {table_id}")
