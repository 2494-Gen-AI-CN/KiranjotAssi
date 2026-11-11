from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


BLUE = "#2563EB"
ORANGE = "#EA580C"

analysis = Path(__file__).resolve().parent
results = pd.read_csv(analysis / "results" / "price_cut.csv")

results = results.sort_values("baseline_cost_per_m", ascending=False).head(15)
actual = "after_cost_per_m" in results.columns
after_column = "after_cost_per_m" if actual else "scenario_cost_per_m"
positions = list(range(len(results)))
fig, ax = plt.subplots(figsize=(14, 9), layout="constrained", facecolor="white")
ax.set_facecolor("white")
ax.barh([y - 0.18 for y in positions], results["baseline_cost_per_m"],
        height=0.34, color=BLUE)
ax.barh([y + 0.18 for y in positions], results[after_column],
        height=0.34, color=ORANGE)
ax.set_yticks(positions, results["model_id"])
ax.invert_yaxis()
ax.set_xlabel("USD per million blended tokens")
if actual:
    reduction = results["cost_reduction_pct"].iloc[0]
    date = pd.to_datetime(results["price_cut_date"].iloc[0]).strftime("%B %d, %Y")
    ax.set_title(f"OpenAI cut o3's price by {reduction:g}% on {date}")
    ax.set_ylim(len(results) - 0.6, -0.6)
else:
    ax.set_title("20% price-cut scenario")
ax.grid(axis="x", alpha=0.25)
ax.legend(
    handles=[
        Patch(facecolor=BLUE, label="Before cut" if actual else "Observed snapshot price"),
        Patch(facecolor=ORANGE, label="After cut" if actual else "Price after assumed cut"),
    ],
    frameon=False,
    loc="upper right",
)
charts = analysis / "charts"
charts.mkdir(exist_ok=True)
filename = "05_o3_price_cut.png" if actual else "05_price_cut_scenario.png"
fig.savefig(charts / filename, dpi=200)
if plt.get_backend().lower() != "agg":
    plt.show()
plt.close(fig)
