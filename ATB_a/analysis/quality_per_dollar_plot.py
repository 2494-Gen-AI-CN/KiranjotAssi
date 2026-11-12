"""Show the highest observed Arena preference score at each token budget."""

import argparse
from math import cos, pi, sin
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import NullFormatter, PercentFormatter, StrMethodFormatter
from matplotlib.transforms import Bbox


BLUE = "#2563EB"
ORANGE = "#EA580C"


def label_points(ax, rows, frontier_color, muted):
    """Place short number labels around the points without overlapping."""
    figure = ax.figure
    figure.canvas.draw()
    pixels_per_point = figure.dpi / 72
    coordinates = ax.transData.transform(rows[["price", "strength"]].to_numpy())
    occupied = [
        Bbox.from_bounds(x - 4, y - 4, 8, 8) for x, y in coordinates
    ]
    bounds = ax.bbox
    offsets = [
        (radius * cos(angle * pi / 4), radius * sin(angle * pi / 4))
        for radius in (10, 15, 21, 29, 39, 52, 68, 85)
        for angle in (1, 7, 3, 5, 0, 4, 2, 6)
    ]
    for row, (x, y) in zip(rows.itertuples(), coordinates):
        width = (5 * len(str(row.label_number)) + 2) * pixels_per_point
        height = 9 * pixels_per_point
        offset = offsets[-1]
        for dx, dy in offsets:
            center_x, center_y = x + dx * pixels_per_point, y + dy * pixels_per_point
            label = Bbox.from_bounds(center_x - width / 2, center_y - height / 2, width, height)
            if (
                bounds.contains(label.x0, label.y0)
                and bounds.contains(label.x1, label.y1)
                and all(not label.overlaps(other) for other in occupied)
            ):
                occupied.append(label)
                offset = (dx, dy)
                break
        color = frontier_color if row.frontier else muted
        ax.annotate(
            str(row.label_number), (row.price, row.strength),
            xytext=offset, textcoords="offset points",
            ha="center", va="center", fontsize=8, fontweight="bold", color="#16253A",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6},
            arrowprops={"arrowstyle": "-", "color": color, "linewidth": 0.45,
                        "shrinkA": 1, "shrinkB": 3},
            zorder=5,
        )


def draw_chart(results):
    eligible = results.loc[results["price"].gt(0) & results["scored_battles"].ge(100)].copy()
    eligible = eligible.sort_values(["strength", "model_id"], ascending=[False, True])
    eligible["label_number"] = range(1, len(eligible) + 1)
    eligible["frontier"] = eligible["is_pareto_frontier"].astype(str).str.lower().eq("true")
    frontier = eligible.loc[eligible["frontier"]].sort_values("price")
    if frontier.empty:
        raise ValueError("The CSV has no eligible frontier models. Export the BigQuery result first.")

    ink, muted, frontier_color = "#16253A", "#52647B", ORANGE
    fig = plt.figure(figsize=(19, 9.5), facecolor="white")
    ax = fig.add_axes([0.06, 0.16, 0.53, 0.68])
    fig.text(0.06, 0.94, "Quality Per Dollar",
             fontsize=25, fontweight="bold", color=ink)

    other = eligible.loc[~eligible.index.isin(frontier.index)]
    ax.scatter(other["price"], other["strength"], s=36, color=BLUE,
               label="Other eligible models", zorder=2)
    right = eligible["price"].max() * 1.23
    ax.step([*frontier["price"], right], [*frontier["strength"], frontier["strength"].iloc[-1]],
            where="post", color=frontier_color, linewidth=2.4, label="Best score within budget", zorder=3)
    ax.scatter(frontier["price"], frontier["strength"], color=frontier_color, s=58,
               edgecolor="white", linewidth=0.9, zorder=4)

    left = eligible["price"].min() / 1.24
    ax.set_xscale("log")
    ax.set_xlim(left, right)
    ax.set_ylim(max(0, eligible["strength"].min() - 0.05),
                min(1, eligible["strength"].max() + 0.085))
    ax.set_xticks([tick for tick in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50) if left < tick < right])
    ax.xaxis.set_major_formatter(StrMethodFormatter("${x:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xlabel("Budget per million blended tokens (USD, log scale)", labelpad=10)
    ax.set_ylabel("Mean Arena preference score", labelpad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#E3E9EF")
    ax.set_axisbelow(True)
    label_points(ax, eligible, frontier_color, muted)
    ax.legend(loc="upper right", frameon=False)

    fig.text(0.63, 0.84, "Model key", fontsize=14, fontweight="bold", color=ink)
    rows_per_column = (len(eligible) + 1) // 2
    spacing = 0.69 / max(rows_per_column, 1)
    for index, row in enumerate(eligible.itertuples()):
        column, position = divmod(index, rows_per_column)
        x, y = 0.63 + column * 0.181, 0.803 - position * spacing
        fig.text(x, y, f"{row.label_number:>2}", fontsize=8, fontweight="bold", color=ink)
        fig.text(x + 0.019, y, row.model_id, fontsize=8, color=ink)
        if row.frontier:
            fig.text(x - 0.009, y, "●", fontsize=7, color=frontier_color)

    return fig


def draw_panel(fig, rows, left, panel_size, start):
    frontier = rows["is_pareto_frontier"].astype(str).str.lower().eq("true")
    priced = rows["price"].notna()
    colors = [
        ORANGE if best else BLUE if has_price else "#7B8794"
        for best, has_price in zip(frontier, priced)
    ]

    ax = fig.add_axes([left + 0.22, 0.105, 0.205, 0.74])
    positions = range(len(rows))
    ax.barh(positions, rows["strength"], color=colors, height=0.63)
    ax.set_yticks(positions, rows["model_id"], fontsize=9)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.set_ylim(panel_size - 0.5, -0.5)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Mean Arena preference score", fontsize=11)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#E2E7ED")
    ax.spines[["top", "right", "left"]].set_visible(False)

    fig.text(
        left + 0.02, 0.865, f"Models {start + 1}–{start + len(rows)}",
        fontsize=12, fontweight="bold", color="#152238",
    )
    ax.text(
        1.045, 1.025, "Price / 1M", transform=ax.transAxes,
        fontsize=9, fontweight="bold", color="#152238",
    )
    for position, price in enumerate(rows["price"]):
        label = f"${price:,.3f}".rstrip("0").rstrip(".") if pd.notna(price) else "—"
        ax.text(
            1.045, position, label, transform=ax.get_yaxis_transform(),
            va="center", fontsize=9, color="#152238",
        )


def build_chart(results):
    rows = results.sort_values(["strength", "model_id"], ascending=[False, True])
    frontier = rows["is_pareto_frontier"].astype(str).str.lower().eq("true")
    panel_size = (len(rows) + 1) // 2
    fig = Figure(figsize=(17.5, max(7, panel_size * 0.27 + 1.8)), dpi=96, facecolor="white")
    draw_panel(fig, rows.iloc[:panel_size], left=0.005, panel_size=panel_size, start=0)
    draw_panel(fig, rows.iloc[panel_size:], left=0.50, panel_size=panel_size, start=panel_size)

    fig.text(
        0.025, 0.972, f"Arena preference scores · all {len(rows)} models",
        va="top", fontsize=21, fontweight="bold", color="#152238",
    )
    fig.text(
        0.025, 0.928,
        f"{int(rows['price'].notna().sum())} matched prices · {int(frontier.sum())} on the frontier · "
        "OpenRouter and manual rates from multiple dates",
        va="top", fontsize=11, color="#475467",
    )
    fig.text(
        0.025, 0.026,
        "Orange: frontier   ·   Blue: other priced models   ·   Gray / dash: no matched price"
        "   ·   USD per million tokens at a 50/50 input/output mix",
        fontsize=9, color="#475467",
    )
    return fig


def show_chart(fig):
    import tkinter as tk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    window = tk.Tk()
    window.title("Arena preference scores")
    window.state("zoomed")

    plot = FigureCanvasTkAgg(fig, master=window)
    plot.get_tk_widget().pack(fill="both", expand=True)
    plot.draw_idle()
    window.mainloop()



def main():
    parser = argparse.ArgumentParser()
    display = parser.add_mutually_exclusive_group()
    display.add_argument("--save-only", action="store_true")
    display.add_argument("--all-models", action="store_true",
                         help="Open the two-panel chart instead of the budget frontier.")
    args = parser.parse_args()
    analysis = Path(__file__).resolve().parent
    results = pd.read_csv(analysis / "results" / "quality_per_dollar.csv")
    charts = analysis / "charts"
    charts.mkdir(exist_ok=True)

    budget_chart = draw_chart(results)
    model_chart = build_chart(results)
    print(f"Saved both quality-per-dollar charts to {charts}")

    if args.all_models:
        plt.close(budget_chart)
        show_chart(model_chart)
    elif not args.save_only:
        plt.show()
    plt.close(budget_chart)


if __name__ == "__main__":
    main()
