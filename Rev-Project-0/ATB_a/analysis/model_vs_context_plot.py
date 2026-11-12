"""Plot Arena rank changes with the presentation palette."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BLUE, ORANGE = "#2563EB", "#EA580C"
CREAM, INK, MUTED = "#FFFFFF", "#152238", "#475467"
PROVIDERS = {
    "gemini-2.5-pro": "Google",
    "chatgpt-4o-latest-20250326": "OpenAI",
    "claude-opus-4-20250514-thinking-16k": "Anthropic",
    "claude-sonnet-4-20250514-thinking-32k": "Anthropic",
    "claude-3-7-sonnet-20250219-thinking-32k": "Anthropic",
    "hunyuan-turbos-20250416": "Tencent",
    "claude-3-7-sonnet-20250219": "Anthropic",
    "claude-3-5-sonnet-20241022": "Anthropic",
}

analysis = Path(__file__).resolve().parent
results = pd.read_csv(analysis / "results" / "model_vs_context.csv")

# Show the six biggest moves and up to two models that kept their rank.
biggest_moves = results.loc[results["style_rank_shift"].abs().nlargest(6).index]
stable = results.loc[results["style_rank_shift"].eq(0)].nsmallest(2, "raw_rank")
shown = pd.concat([biggest_moves, stable]).drop_duplicates("model_name")
shown = shown.sort_values("style_controlled_rank")

fig, ax = plt.subplots(figsize=(15, 7.2), facecolor=CREAM)
fig.subplots_adjust(left=0.38, right=0.855, top=0.735, bottom=0.205)
ax.set_facecolor(CREAM)

largest_shift = results["style_rank_shift"].abs().max()
snapshot = pd.to_datetime(results["snapshot_date"].iloc[0])
date_label = f"{snapshot:%B} {snapshot.day}, {snapshot:%Y}"
fig.text(
    0.055, 0.925, f"Model vs. Context",
    color=INK, fontsize=24, fontweight="bold",
)

positions = range(len(shown))
ax.hlines(
    positions, shown["raw_rank"], shown["style_controlled_rank"],
    color="#AEB8C4", linewidth=1.6, zorder=2,
)
ax.scatter(
    shown["raw_rank"], positions, color=BLUE, s=112, label="Raw rank", zorder=3,
)
ax.scatter(
    shown["style_controlled_rank"], positions, color=ORANGE, marker="D", s=46,
    edgecolor=CREAM, linewidth=0.7, label="Style-controlled rank", zorder=4,
)
fig.legend(loc="upper left", bbox_to_anchor=(0.38, 0.817), ncol=2, frameon=False)

labels = [
    f"{name} [{PROVIDERS[name]}]" if name in PROVIDERS else name
    for name in shown["model_name"]
]
ax.set_yticks(positions, labels, fontsize=10, color=INK)
ax.set_ylim(len(shown) - 0.5, -0.5)
ax.set_xlim(0.2, len(results) + 0.8)
ax.set_xticks([1, *range(5, len(results) + 1, 5)])
ax.set_xlabel("Rank within the matched group (1 is best)", labelpad=11)
ax.tick_params(axis="y", length=0, pad=11)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#A9ADB4")
ax.set_axisbelow(True)
ax.grid(axis="x", color="#DBD8D2", linewidth=0.8)

ax.text(1.045, 1.025, "Rank change", transform=ax.transAxes,
        color=INK, fontsize=10, fontweight="bold")
for position, row in enumerate(shown.itertuples()):
    shift = int(row.style_rank_shift)
    change = f"Up {abs(shift)}" if shift < 0 else f"Down {shift}" if shift > 0 else "Held"
    ax.text(
        1.045, position, change, transform=ax.get_yaxis_transform(),
        va="center", color=INK, fontsize=10,
    )

rose = results["style_rank_shift"].lt(0).sum()
fell = results["style_rank_shift"].gt(0).sum()
held = results["style_rank_shift"].eq(0).sum()

charts = analysis / "charts"
charts.mkdir(exist_ok=True)
if plt.get_backend().lower() != "agg":
    plt.show()
plt.close(fig)
