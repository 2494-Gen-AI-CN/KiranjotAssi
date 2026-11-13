from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from google.cloud import bigquery

from src.config import PROJECT_ID, DATASET_ID


OUTPUT_DIR = Path("reports/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = bigquery.Client(project=PROJECT_ID)


def query_df(sql):
    return client.query(sql).to_dataframe()


def save_chart(fig, filename):
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {OUTPUT_DIR / filename}")


# ------------------------------------------------------------
# Chart 1 — Use Case 1: Open vs. closed strength gap
# ------------------------------------------------------------

def plot_open_closed_gap():
    sql = f"""
        SELECT
          release,
          open_closed_gap
        FROM `{PROJECT_ID}.{DATASET_ID}.fact_open_closed_gap`
        ORDER BY CASE release
          WHEN '100k_2024' THEN 1
          WHEN '140k_2025' THEN 2
          ELSE 3
        END
    """
    df = query_df(sql)

    labels = df["release"].map({
        "100k_2024": "2024 release",
        "140k_2025": "2025 release",
    }).fillna(df["release"])

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, df["open_closed_gap"], color="#4285F4", width=0.55)

    ax.bar_label(bars, fmt="%.1f", padding=4)
    ax.set_title("The estimated open–closed strength gap was wider in 2025")
    ax.set_ylabel("Closed strength minus open strength (Elo points)")
    ax.set_xlabel("Arena release")
    ax.set_ylim(0, max(df["open_closed_gap"]) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)

    save_chart(fig, "use_case_1_open_closed_gap.png")


# ------------------------------------------------------------
# Chart 2 — Use Case 2: English vs. Chinese language gaps
# ------------------------------------------------------------

def plot_language_gaps():
    sql = f"""
        SELECT
          model,
          MAX(IF(language = 'English', language_gap, NULL)) AS english_gap,
          MAX(IF(language = 'Chinese', language_gap, NULL)) AS chinese_gap,
          SUM(language_battles) AS total_battles
        FROM `{PROJECT_ID}.{DATASET_ID}.fact_model_language_gap_shared_anchor`
        WHERE release = '100k_2024'
          AND language IN ('English', 'Chinese')
          AND language_battles >= 200
        GROUP BY model
        HAVING COUNTIF(language = 'English') > 0
           AND COUNTIF(language = 'Chinese') > 0
        ORDER BY total_battles DESC
        LIMIT 5
    """
    df = query_df(sql)

    x = np.arange(len(df))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(x - width / 2, df["english_gap"], width,
           label="English", color="#4285F4")
    ax.bar(x + width / 2, df["chinese_gap"], width,
           label="Chinese", color="#FB8C00")

    labels = df["model"].str.replace("-instruct", "", regex=False)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.axhline(0, color="#444444", linewidth=0.8)
    ax.set_title("The displayed models had lower relative strength on Chinese prompts")
    ax.set_ylabel("Language-specific gap from model's overall strength (Elo points)")
    ax.set_xlabel("Model")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    save_chart(fig, "use_case_2_language_gaps_2024.png")


# ------------------------------------------------------------
# Chart 3 — Use Case 2: Prompt-length gaps
# ------------------------------------------------------------

def plot_prompt_length_gaps():
    sql = f"""
        WITH eligible_models AS (
          SELECT model
          FROM `{PROJECT_ID}.{DATASET_ID}.fact_model_prompt_length_gap`
          WHERE release = '140k_2025'
            AND language = 'English'
            AND bucket_battles >= 200
          GROUP BY model
          HAVING COUNT(DISTINCT prompt_length_bucket) = 4
        )
        SELECT
          p.model,
          p.prompt_length_bucket,
          p.prompt_length_gap,
          p.bucket_battles
        FROM `{PROJECT_ID}.{DATASET_ID}.fact_model_prompt_length_gap` AS p
        JOIN eligible_models USING (model)
        WHERE p.release = '140k_2025'
          AND p.language = 'English'
          AND p.bucket_battles >= 200
    """
    df = query_df(sql)

    # Show the 12 models with the most battles across all four buckets.
    selected = (
        df.groupby("model")["bucket_battles"]
          .sum()
          .nlargest(12)
          .index
    )
    df = df[df["model"].isin(selected)]

    bucket_order = [
        "Q1 - shortest",
        "Q2",
        "Q3",
        "Q4 - longest",
    ]

    matrix = (
        df.pivot(index="model",
                 columns="prompt_length_bucket",
                 values="prompt_length_gap")
          .reindex(columns=bucket_order)
    )

    # Order rows by battle volume so the most represented models appear first.
    model_order = (
        df.groupby("model")["bucket_battles"]
          .sum()
          .sort_values(ascending=False)
          .index
    )
    matrix = matrix.reindex(model_order)

    values = matrix.to_numpy()
    limit = max(50, np.nanmax(np.abs(values)))

    fig, ax = plt.subplots(figsize=(10, 7))
    image = ax.imshow(values, cmap="RdBu_r", aspect="auto",
                      vmin=-limit, vmax=limit)

    ax.set_xticks(range(len(bucket_order)))
    ax.set_xticklabels(["Shortest", "Q2", "Q3", "Longest"])
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_title("Relative strength varies across prompt-length buckets")
    ax.set_xlabel("Prompt length bucket")
    ax.set_ylabel("Model")

    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            if not np.isnan(values[row, col]):
                ax.text(col, row, f"{values[row, col]:.0f}",
                        ha="center", va="center", fontsize=8)

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Gap from model's overall strength (Elo points)")

    save_chart(fig, "use_case_2_prompt_length_gaps_2025.png")


# ------------------------------------------------------------
# Chart 4 — Use Case 3: Price vs. strength decision matrix
# ------------------------------------------------------------

def plot_price_strength():
    sql = f"""
        SELECT
          model,
          blended_usd_per_m,
          strength_elo,
          battle_count,
          matrix_quadrant,
          median_price,
          median_strength
        FROM `{PROJECT_ID}.{DATASET_ID}.fact_decision_matrix`
        WHERE blended_usd_per_m IS NOT NULL
          AND strength_elo IS NOT NULL
    """
    df = query_df(sql)
    top3 = (
        df[df["matrix_quadrant"].str.startswith("Higher strength, lower price")]
        .nlargest(3, "strength_elo")
    )

    colors = {
        "Higher strength, lower price — best value": "#2CA02C",
        "Higher strength, higher price — premium": "#FF7F0E",
        "Lower strength, lower price — budget": "#4285F4",
        "Lower strength, higher price — weak value": "#D62728",
    }

    fig, ax = plt.subplots(figsize=(9, 6))

    for quadrant, group in df.groupby("matrix_quadrant"):
        color = colors.get(quadrant, "#777777")
        label = quadrant.replace(" — ", "\n")
        ax.scatter(
            group["blended_usd_per_m"],
            group["strength_elo"],
            s=55,
            alpha=0.85,
            color=color,
            label=label,
        )

    ax.scatter(
        top3["blended_usd_per_m"],
        top3["strength_elo"],
        marker="*",
        s=240,
        color="#E4572E",
        edgecolors="black",
        linewidths=0.7,
        zorder=10,
        label="Top 3 by Arena strength",
        )

    for _, row in top3.iterrows():
        ax.annotate(
            row["model"],
            (row["blended_usd_per_m"], row["strength_elo"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
        )
    

    median_price = df["median_price"].iloc[0]
    median_strength = df["median_strength"].iloc[0]
    correlation = df["blended_usd_per_m"].corr(df["strength_elo"])

    ax.axvline(median_price, color="#666666", linestyle="--", linewidth=1)
    ax.axhline(median_strength, color="#666666", linestyle="--", linewidth=1)

    ax.set_title(
        f"Price and Arena strength had little linear association "
        f"(34 matched models, r = {correlation:.2f})"
    )
    ax.set_xlabel("Blended price (USD per 1M tokens; equal input/output mix)")
    ax.set_ylabel("Arena strength (Elo points)")
    ax.legend(title="Median-based group", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    save_chart(fig, "use_case_3_price_vs_strength.png")


if __name__ == "__main__":
    plot_open_closed_gap()
    plot_language_gaps()
    plot_prompt_length_gaps()
    plot_price_strength()