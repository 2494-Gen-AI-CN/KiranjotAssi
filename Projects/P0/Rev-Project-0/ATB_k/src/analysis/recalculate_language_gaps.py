import math
from collections import Counter, defaultdict

from google.cloud import bigquery
from src.config import PROJECT_ID, DATASET_ID


MIN_BATTLES = 200
MIN_SHARED_MODELS = 3
ELO_FACTOR = 400 / math.log(10)
LANGUAGES = ("English", "Chinese")

QUERY = f"""
SELECT
  b.release,
  CASE
    WHEN LOWER(TRIM(b.language)) IN ('en', 'english')
      THEN 'English'
    WHEN LOWER(TRIM(b.language)) IN ('zh', 'chinese', 'zh-hans', 'zh-hant')
      THEN 'Chinese'
    ELSE NULL
  END AS language,
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
WHERE b.winner_side IN ('model_a', 'model_b')
"""


def fit_bradley_terry(battles):
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

    all_battles = defaultdict(list)
    language_battles = defaultdict(list)
    open_status = {}

    for row in client.query(QUERY).result():
        release = row["release"]
        model_a = row["model_a"]
        model_b = row["model_b"]

        if model_a == model_b:
            continue

        winner = model_a if row["winner_side"] == "model_a" else model_b
        battle = (model_a, model_b, winner)

        # Overall strength uses all mapped decisive battles in the release.
        all_battles[release].append(battle)

        if row["language"] in LANGUAGES:
            language_battles[(release, row["language"])].append(battle)

        open_status[(release, model_a)] = row["model_a_open"]
        open_status[(release, model_b)] = row["model_b_open"]

    output = []

    for release, release_battles in all_battles.items():
        overall_elo, overall_counts = fit_bradley_terry(release_battles)

        fits = {}
        eligible_sets = []

        for language in LANGUAGES:
            battles = language_battles.get((release, language), [])
            language_elo, language_counts = fit_bradley_terry(battles)

            eligible = {
                model
                for model, count in language_counts.items()
                if count >= MIN_BATTLES
                and overall_counts[model] >= MIN_BATTLES
                and model in overall_elo
                and model in language_elo
            }

            if not eligible:
                break

            fits[language] = (language_elo, language_counts)
            eligible_sets.append(eligible)

        if len(eligible_sets) != len(LANGUAGES):
            print(f"Skipping {release}: English or Chinese has no qualifying models")
            continue

        # The identical anchor cohort is used for both language comparisons.
        shared_models = set.intersection(*eligible_sets)

        if len(shared_models) < MIN_SHARED_MODELS:
            print(
                f"Skipping {release}: only {len(shared_models)} models "
                "qualify in both English and Chinese"
            )
            continue

        overall_anchor_mean = sum(
            overall_elo[model] for model in shared_models
        ) / len(shared_models)

        print(f"{release}: {len(shared_models)} shared English/Chinese models")

        for language in LANGUAGES:
            language_elo, language_counts = fits[language]
            language_anchor_mean = sum(
                language_elo[model] for model in shared_models
            ) / len(shared_models)

            for model in sorted(shared_models):
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
                    "anchor_models": len(shared_models),
                })

    if not output:
        raise ValueError(
            "No comparable English/Chinese results were produced. "
            "Check language labels and model coverage."
        )

    table_id = (
        f"{PROJECT_ID}.{DATASET_ID}.fact_model_language_gap_shared_anchor"
    )
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
    for result in sorted(output, key=lambda item: item["language_gap"])[:10]:
        print(result)


if __name__ == "__main__":
    main()