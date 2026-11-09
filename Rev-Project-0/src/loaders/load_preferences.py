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

    # The 100k release uses Unix timestamps; the 140k release uses timestamps.
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    return pd.to_datetime(value, utc=True, errors="coerce")


def content_to_text(content):
    """Extract text from either plain strings or structured content blocks."""
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, dict):
        return content.get("text") or ""

    if isinstance(content, list):
        return "".join(content_to_text(part) for part in content)

    return ""


def user_chars(conversation):
    """Count characters in user messages, excluding model responses."""
    total = 0

    for message in conversation or []:
        if isinstance(message, dict) and message.get("role") == "user":
            total += len(content_to_text(message.get("content")))

    return total


def get_prompt_chars(row):
    """Average the user-message character counts for both sides of a battle."""
    chars_a = user_chars(row.get("conversation_a"))
    chars_b = user_chars(row.get("conversation_b"))

    if chars_a and chars_b:
        return round((chars_a + chars_b) / 2)

    return chars_a or chars_b


rows = []

for release, repo_id in RELEASES.items():
    print(f"Loading {release} from {repo_id}...")

    dataset = load_dataset(repo_id, split="train", streaming=True)

    for row in dataset:
        rows.append({
            "release": release,
            "source-dataset": repo_id,
            "vote_timestamp": normalize_timestamp(
                first_present(row, ["timestamp", "tstamp"])
            ),
            "model_a": first_present(row, ["model_a"]),
            "model_b": first_present(row, ["model_b"]),
            "winner_raw": first_present(row, ["winner", "actual_score"]),
            "language": first_present(row, ["language", "language_tag"]),
            "prompt_chars": get_prompt_chars(row),
        })

df = pd.DataFrame(rows)

# Keep this as a nullable integer column when some rows lack user text.
df["prompt_chars"] = pd.array(df["prompt_chars"], dtype="Int64")

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
print(f"Rows with missing prompt length: {df['prompt_chars'].isna().sum()}")