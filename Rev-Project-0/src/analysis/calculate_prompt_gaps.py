import math
from collections import Counter, defaultdict

from google.cloud import bigquery
from src.config import PROJECT_ID, DATASET_ID


MIN_BATTLES = 200
ELO_FACTOR = 400 / math.log(10)

BUCKETS = [
    "Q1 - shortest",
    "Q2",
    "Q3",
    "Q4 - longest",
]

QUERY = f"""
SELECT
  b.release,
  b.prompt_length_bucket,
  ma.canonical_model_id AS model_a,
  mb.canonical_model_id AS model_b,
  b.winner_side,
  ma.is_open_weight AS model_a_open,
  mb.is_open_weight AS model_b_open
FROM `{PROJECT_ID}.{DATASET_ID}.fact_preference_battle` AS b
JOIN `{PROJECT_ID}.{DATASET_ID}.model_mapping` AS ma
  ON ma.release = b.release
 AND ma.source_model_name = b.source_model_a
JOIN `{PROJECT_ID}.{DATASET_ID}.model_mapping` AS mb
  ON mb.release = b.release
 AND mb.source_model_name = b.source_model_b
WHERE LOWER(TRIM(b.language)) IN ('english', 'en')
  AND b.prompt_length_bucket IN (
    'Q1 - shortest', 'Q2', 'Q3', 'Q4 - longest'
  )
  AND b.winner_side IN ('model_a', 'model_b')
"""


def fit_bradley_terry(battles):
    """Fit Bradley–Terry strengths and return Elo ratings plus battle counts."""
    wins = Counter()
    appearances = Counter()
    pair_counts = defaultdict(Counter)
    models = set()

    for model_a, model_b, winner in battles:
        if model_a == model_b:
            continue

        models.update((model_a, model_b))
        appearances[model_a] += 1
        appearances[model_b] += 1
        wins[winner] += 1
        pair_counts[model_a][model_b] += 1
        pair_counts[model_b][model_a] += 1

    if len(models) < 2:
        return {}, appearances

    strengths = {model: 1.0 for model in models}
    epsilon = 1e-12

    for _ in range(10000):
        updated = {}

        for model in models:
            denominator = sum(
                count / (strengths[model] + strengths[opponent])
                for opponent, count in pair_counts[model].items()
            )
            updated[model] = max(wins[model] / denominator, epsilon)

        # BT strengths are relative, so center each fit at geometric mean 1.
        mean_log = sum(math.log(value) for value in updated.values()) / len(updated)
        updated = {
            model: value / math.exp(mean_log)
            for model, value in updated.items()
        }

        change = max(
            abs(math.log(updated[model] / strengths[model]))
                for model in models
        )
        strengths = updated

        if change < 1e-8:
            break

    elo = {
        model: ELO_FACTOR * math.log(value)
        for model, value in strengths.items()
    }
    return elo, appearances


def main():
    client = bigquery.Client(project=PROJECT_ID)
    rows = client.query(QUERY).result()

    battles_by_release = defaultdict(list)
    battles_by_release_bucket = defaultdict(list)
    bucket_counts = defaultdict(Counter)
    open_status = {}

    for row in rows:
        model_a = row["model_a"]
        model_b = row["model_b"]

        if model_a == model_b:
            continue

        release = row["release"]
        bucket = row["prompt_length_bucket"]
        winner = model_a if row["winner_side"] == "model_a" else model_b
        battle = (model_a, model_b, winner)

        battles_by_release[release].append(battle)
        battles_by_release_bucket[(release, bucket)].append(battle)

        bucket_counts[(release, bucket)][model_a] += 1
        bucket_counts[(release, bucket)][model_b] += 1

        open_status[(release, model_a)] = row["model_a_open"]
        open_status[(release, model_b)] = row["model_b_open"]

    output = []

    for release, overall_battles in battles_by_release.items():
        # Keep models with at least 200 decisive battles in every bucket.
        eligible = set.intersection(*[
            {
                model
                for model, count in bucket_counts[(release, bucket)].items()
                if count >= MIN_BATTLES
            }
            for bucket in BUCKETS
        ])

        if len(eligible) < 2:
            print(f"Skipping {release}: fewer than 2 models qualify in all buckets")
            continue

        overall_elo, overall_counts = fit_bradley_terry(overall_battles)

        # Use this same eligible group to align every bucket and overall rating.
        overall_anchor_mean = sum(
            overall_elo[model] for model in eligible
        ) / len(eligible)

        print(f"{release}: {len(eligible)} models qualify in all four buckets")

        for bucket in BUCKETS:
            bucket_battles = battles_by_release_bucket.get((release, bucket), [])
            bucket_elo, bucket_appearances = fit_bradley_terry(bucket_battles)

            bucket_anchor_mean = sum(
                bucket_elo[model] for model in eligible
            ) / len(eligible)

            for model in sorted(eligible):
                gap = (
                    bucket_elo[model] - bucket_anchor_mean
                    - (overall_elo[model] - overall_anchor_mean)
                )

                output.append({
                    "release": release,
                    "language": "English",
                    "prompt_length_bucket": bucket,
                    "model": model,
                    "is_open_weight": open_status.get((release, model)),
                    "bucket_battles": bucket_appearances[model],
                    "overall_battles": overall_counts[model],
                    "elo_bucket": bucket_elo[model],
                    "elo_overall": overall_elo[model],
                    "prompt_length_gap": gap,
                    "anchor_models": len(eligible),
                })

    if not output:
        raise ValueError("No results were produced. Check bucket labels and model mappings.")

    table_id = f"{PROJECT_ID}.{DATASET_ID}.fact_model_prompt_length_gap"
    schema = [
        bigquery.SchemaField("release", "STRING"),
        bigquery.SchemaField("language", "STRING"),
        bigquery.SchemaField("prompt_length_bucket", "STRING"),
        bigquery.SchemaField("model", "STRING"),
        bigquery.SchemaField("is_open_weight", "BOOL"),
        bigquery.SchemaField("bucket_battles", "INT64"),
        bigquery.SchemaField("overall_battles", "INT64"),
        bigquery.SchemaField("elo_bucket", "FLOAT64"),
        bigquery.SchemaField("elo_overall", "FLOAT64"),
        bigquery.SchemaField("prompt_length_gap", "FLOAT64"),
        bigquery.SchemaField("anchor_models", "INT64"),
    ]

    job = client.load_table_from_json(
        output,
        table_id,
        job_config=bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_TRUNCATE",
        ),
    )
    job.result()

    print(f"Wrote {len(output)} rows to {table_id}")
    for result in sorted(output, key=lambda item: item["prompt_length_gap"])[:10]:
        print(result)


if __name__ == "__main__":
    main()