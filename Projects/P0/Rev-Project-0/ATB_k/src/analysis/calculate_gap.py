import math
from collections import Counter, defaultdict

from google.cloud import bigquery
from src.config import PROJECT_ID, DATASET_ID

MIN_BATTLES = 50
MAX_ITERATIONS = 20_000
LEARNING_RATE = 1.0
REGULARIZATION = 0.01
TOLERANCE = 1e-8

client = bigquery.Client(project=PROJECT_ID)

query = f"""
SELECT
  f.release,
  f.winner_side,
  f.source_model_a,
  f.source_model_b,
  ma.canonical_model_id AS model_a_id,
  mb.canonical_model_id AS model_b_id,
  ma.is_open_weight AS model_a_is_open,
  mb.is_open_weight AS model_b_is_open
FROM `{PROJECT_ID}.{DATASET_ID}.fact_preference_battle` AS f
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.model_mapping` AS ma
  ON ma.release = f.release
 AND ma.source_model_name = f.source_model_a
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.model_mapping` AS mb
  ON mb.release = f.release
 AND mb.source_model_name = f.source_model_b
"""

# Store decisive, mapped battles grouped by release.
periods = defaultdict(lambda: {
    "pairs": defaultdict(lambda: [0, 0]),  # A wins, B wins
    "appearances": Counter(),
    "status": defaultdict(set),
    "eligible_battles": 0,
})

total_rows = 0
decisive_rows = 0
mapped_rows = 0
self_matches = 0

for row in client.query(query).result():
    total_rows += 1

    if row["winner_side"] not in ("model_a", "model_b"):
        continue
    decisive_rows += 1

    if (
        not row["release"]
        or not row["model_a_id"]
        or not row["model_b_id"]
        or row["model_a_is_open"] is None
        or row["model_b_is_open"] is None
    ):
        continue
    mapped_rows += 1

    model_a = row["model_a_id"]
    model_b = row["model_b_id"]

    if model_a == model_b:
        self_matches += 1
        continue

    period = periods[row["release"]]
    pair = period["pairs"][(model_a, model_b)]

    if row["winner_side"] == "model_a":
        pair[0] += 1
    else:
        pair[1] += 1

    period["appearances"][model_a] += 1
    period["appearances"][model_b] += 1
    period["status"][model_a].add(bool(row["model_a_is_open"]))
    period["status"][model_b].add(bool(row["model_b_is_open"]))
    period["eligible_battles"] += 1

print(f"Rows in battle fact: {total_rows:,}")
print(f"Decisive A/B wins: {decisive_rows:,}")
print(f"Decisive wins with both models mapped: {mapped_rows:,}")
print(f"Same-model matches excluded: {self_matches:,}")
print(f"Battles used for rating: {sum(p['eligible_battles'] for p in periods.values()):,}")

if not periods:
    raise ValueError(
        "No eligible battles remain. Check fact_preference_battle "
        "and populate model_mapping."
    )


def sigmoid(value):
    # Stable logistic function.
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def fit_bradley_terry(period):
    model_ids = sorted(period["appearances"])
    index = {model_id: i for i, model_id in enumerate(model_ids)}
    pairs = []

    for (model_a, model_b), (wins_a, wins_b) in period["pairs"].items():
        pairs.append((index[model_a], index[model_b], wins_a, wins_b))

    total_votes = sum(wins_a + wins_b for _, _, wins_a, wins_b in pairs)
    ratings = [0.0] * len(model_ids)

    # Gradient ascent on the regularized Bradley–Terry likelihood.
    for _ in range(MAX_ITERATIONS):
        gradient = [-REGULARIZATION * rating for rating in ratings]

        for a_idx, b_idx, wins_a, wins_b in pairs:
            count = wins_a + wins_b
            probability_a = sigmoid(ratings[a_idx] - ratings[b_idx])

            gradient[a_idx] += (
                wins_a - count * probability_a
            ) / total_votes

            gradient[b_idx] += (
                wins_b - count * (1.0 - probability_a)
            ) / total_votes

        largest_gradient = max(abs(value) for value in gradient)

        if largest_gradient < TOLERANCE:
            break

        for i, value in enumerate(gradient):
            ratings[i] += LEARNING_RATE * value

    # Convert log-odds strengths to Elo points.
    elo = {
        model_id: ratings[index[model_id]] * (400.0 / math.log(10.0))
        for model_id in model_ids
    }
    return elo


strength_rows = []
gap_rows = []

for release, period in periods.items():
    conflicting = [
        model_id
        for model_id, labels in period["status"].items()
        if len(labels) != 1
    ]
    if conflicting:
        raise ValueError(
            f"Conflicting open/closed labels in {release}: {conflicting[:5]}"
        )

    elo_ratings = fit_bradley_terry(period)

    for model_id, elo in elo_ratings.items():
        strength_rows.append({
            "release": release,
            "canonical_model_id": model_id,
            "is_open_weight": next(iter(period["status"][model_id])),
            "battle_count": int(period["appearances"][model_id]),
            "strength_elo": float(elo),
        })

    qualified = [
        row for row in strength_rows
        if row["release"] == release
        and row["battle_count"] >= MIN_BATTLES
    ]

    open_models = [row for row in qualified if row["is_open_weight"]]
    closed_models = [row for row in qualified if not row["is_open_weight"]]

    if not open_models or not closed_models:
        raise ValueError(
            f"{release} needs an open and a closed model with at least "
            f"{MIN_BATTLES} decisive battles. Verify mappings or review "
            "the threshold."
        )

    best_open = max(open_models, key=lambda row: row["strength_elo"])
    best_closed = max(closed_models, key=lambda row: row["strength_elo"])

    gap_rows.append({
        "release": release,
        "best_open_model": best_open["canonical_model_id"],
        "best_open_strength_elo": best_open["strength_elo"],
        "best_closed_model": best_closed["canonical_model_id"],
        "best_closed_strength_elo": best_closed["strength_elo"],
        "open_closed_gap": (
            best_closed["strength_elo"] - best_open["strength_elo"]
        ),
        "min_battles_threshold": MIN_BATTLES,
        "eligible_battles": period["eligible_battles"],
    })


def replace_table(table_name, rows, schema):
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    client.load_table_from_json(rows, table_id, job_config=config).result()
    print(f"Wrote {len(rows):,} rows to {table_id}")


replace_table(
    "fact_model_strength",
    strength_rows,
    [
        bigquery.SchemaField("release", "STRING"),
        bigquery.SchemaField("canonical_model_id", "STRING"),
        bigquery.SchemaField("is_open_weight", "BOOL"),
        bigquery.SchemaField("battle_count", "INT64"),
        bigquery.SchemaField("strength_elo", "FLOAT64"),
    ],
)

replace_table(
    "fact_open_closed_gap",
    gap_rows,
    [
        bigquery.SchemaField("release", "STRING"),
        bigquery.SchemaField("best_open_model", "STRING"),
        bigquery.SchemaField("best_open_strength_elo", "FLOAT64"),
        bigquery.SchemaField("best_closed_model", "STRING"),
        bigquery.SchemaField("best_closed_strength_elo", "FLOAT64"),
        bigquery.SchemaField("open_closed_gap", "FLOAT64"),
        bigquery.SchemaField("min_battles_threshold", "INT64"),
        bigquery.SchemaField("eligible_battles", "INT64"),
    ],
)

print("\nGap results:")
for result in gap_rows:
    print(result)