from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

analysis = Path(__file__).resolve().parent
results = pd.read_csv(
    analysis / "results" / "model_rating_history.csv",
    parse_dates=["snapshot_date"],
)
if results.empty:
    raise ValueError("The history CSV has no rows. Export the BigQuery results first.")

models = {
    "gemini-2.5-pro": ("Gemini 2.5 Pro [Google]", "#2563EB"),
    "deepseek-r1-0528": ("DeepSeek R1 [DeepSeek]", "#EA580C"),
    "o3-2025-04-16": ("o3 [OpenAI]", "#7C3AED"),
}

fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                         layout="constrained", facecolor="white")
fig.suptitle("How did shortlisted models' ratings change?", fontsize=19, weight="bold")

for model_id, (label, color) in models.items():
    rows = results.loc[results["model_id"].eq(model_id)].sort_values("snapshot_date")
    if rows.empty:
        continue
    dates = rows["snapshot_date"]
    rating = pd.to_numeric(rows["rating"], errors="raise")
    axes[0].plot(dates, rating, color=color, linewidth=2, label=label)
    lower = pd.to_numeric(rows["rating_lower"], errors="coerce")
    upper = pd.to_numeric(rows["rating_upper"], errors="coerce")
    axes[0].fill_between(dates, lower, upper, color=color, alpha=0.10)
    axes[1].plot(dates, rating - rating.iloc[0], color=color, linewidth=2)

axes[0].set_title("Recorded style-controlled ratings", fontsize=11)
axes[0].set_ylabel("Leaderboard rating")
axes[0].legend(loc="best", frameon=False)
axes[1].set_title("Change from the first shared snapshot", fontsize=11)
axes[1].set_ylabel("Rating-point change")
axes[1].axhline(0, color="#64748B", linewidth=1, linestyle="--")
axes[1].set_xlabel("Leaderboard snapshot date")
locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
axes[1].xaxis.set_major_locator(locator)
axes[1].xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
for ax in axes:
    ax.set_facecolor("white")
    ax.grid(axis="y", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)

charts = analysis / "charts"
charts.mkdir(exist_ok=True)
if plt.get_backend().lower() != "agg":
    plt.show()
plt.close(fig)
