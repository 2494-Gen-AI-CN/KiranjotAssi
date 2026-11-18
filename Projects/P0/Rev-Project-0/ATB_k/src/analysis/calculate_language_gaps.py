import math
from collections import Counter, defaultdict

from google.cloud import bigquery
from src.config import PROJECT_ID, DATASET_ID


MIN_BATTLES = 200
ELO_FACTOR = 400 / math.log(10)

QUERY = f"""
WITH normalized AS (
  SELECT
    b.release,
    CASE LOWER(TRIM(b.language))
      WHEN 'en' THEN 'English'
      WHEN 'english' THEN 'English'
      WHEN 'ru' THEN 'Russian'
      WHEN 'russian' THEN 'Russian'
      WHEN 'pl' THEN 'Polish'
      WHEN 'polish' THEN 'Polish'
      WHEN 'zh' THEN 'Chinese'
      WHEN 'chinese' THEN 'Chinese'
      WHEN 'und' THEN NULL
      WHEN 'unknown' THEN NULL
      ELSE NULLIF(TRIM(b.language), '')
    END AS language,
    b.source_model_a,
    b.source_model_b,
    b.winner_side
  FROM `{PROJECT_ID}.{DATASET_ID}.fact_preference_battle` AS b
),
mapped AS (
  SELECT
    n.release,
    n.language,
    ma.canonical_model_id AS model_a,
    mb.canonical_model_id AS model_b,
    n.winner_side,
    ma.is_open_weight AS model_a_open,
    mb.is_open_weight AS model_b_open
  FROM normalized AS n
  JOIN `{PROJECT_ID}.{DATASET_ID}.model_mapping` AS ma
    ON ma.release = n.release
   AND ma.source_model_name = n.source_model_a
  JOIN `{PROJECT_ID}.{DATASET_ID}.model_mapping` AS mb
    ON mb.release = n.release
   AND mb.source_model_name = n.source_model_b
  WHERE n.language IS NOT NULL
    AND n.winner_side IN ('model_a', 'model_b')
)
SELECT *
FROM mapped
"""


def fit_bradley_terry(battles):
    """Return Elo-scale strengths and decisive-battle counts for each model."""
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

    # Bradley–Terry strengths, estimated with the iterative MM update.
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

        # Center each fit at geometric-mean strength 1.
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

    elo = {model: ELO_FACTOR * math.log(value)
           for model, value in strengths.items()}
    return elo, appearances


def main():
    client = bigquery.Client(project=PROJECT_ID)
    rows = client.query(QUERY).result()

    overall_battles = defaultdict(list)
    language_battles = defaultdict(list)
    open_status = {}

    for row in rows:
        model_a = row["model_a"]
        model_b = row["model_b"]
        if model_a == model_b:
            continue

        winner = model_a if row["winner_side"] == "model_a" else model_b
        battle = (model_a, model_b, winner)

        overall_battles[row["release"]].append(battle)
        language_battles[(row["release"], row["language"])].append(battle)

        open_status[(row["release"], model_a)] = row["model_a_open"]
        open_status[(row["release"], model_b)] = row["model_b_open"]

    output = []

    for release, all_battles in overall_battles.items():
        overall_elo, overall_counts = fit_bradley_terry(all_battles)

        for (lang_release, language), battles in language_battles.items():
            if lang_release != release:
                continue

            language_elo, language_counts = fit_bradley_terry(battles)

            # Only compare models with enough data in both the language
            # subset and the overall release.
            eligible = {
                model for model, count in language_counts.items()
                if count >= MIN_BATTLES
                and overall_counts[model] >= MIN_BATTLES
                and model in language_elo
                and model in overall_elo
            }

            # Align the two relative rating scales using the same shared models.
            anchors = eligible & language_elo.keys() & overall_elo.keys()
            if len(anchors) < 2:
                print(f"Skipping {release} / {language}: too few shared models")
                continue

            language_anchor_mean = sum(language_elo[m] for m in anchors) / len(anchors)
            overall_anchor_mean = sum(overall_elo[m] for m in anchors) / len(anchors)

            for model in sorted(eligible):
                gap = (
                    language_elo[model] - language_anchor_mean
                    - (overall_elo[model] - overall_anchor_mean)
                )
                output.append({
                    "release": release,
                    "language": language,
                    "model": model,
                    "is_open_weight": open_status.get((release, model)),
                    "language_battles": language_counts[model],
                    "overall_battles": overall_counts[model],
                    "elo_language": language_elo[model],
                    "elo_overall": overall_elo[model],
                    "language_gap": gap,
                })

    if not output:
        raise ValueError("No model-language rows met the battle threshold.")

    table_id = f"{PROJECT_ID}.{DATASET_ID}.fact_model_language_gap"
    schema = [
        bigquery.SchemaField("release", "STRING"),
        bigquery.SchemaField("language", "STRING"),
        bigquery.SchemaField("model", "STRING"),
        bigquery.SchemaField("is_open_weight", "BOOL"),
        bigquery.SchemaField("language_battles", "INT64"),
        bigquery.SchemaField("overall_battles", "INT64"),
        bigquery.SchemaField("elo_language", "FLOAT64"),
        bigquery.SchemaField("elo_overall", "FLOAT64"),
        bigquery.SchemaField("language_gap", "FLOAT64"),
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
    for row in sorted(output, key=lambda r: r["language_gap"])[:15]:
        print(row)


if __name__ == "__main__":
    main()