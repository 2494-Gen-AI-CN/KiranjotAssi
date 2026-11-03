"""Simple dataset-only plots for stages 2, 4 and 6."""
import matplotlib.pyplot as plt
from reports_a import load_data, value, convenience, ownership_verdict

EV_COLOR = "#F791A9"
CAR_COLOR = "#037F71"

# Optional filters. None means include all available rows.
BODY_TYPE = None
PRICE_BAND = 50000  # Same units as current_market_price; verify the currency.


# Stage 2: Value Check

def plot_value(results):
    """Compare median range across price bands."""
    comparison = results["range_comparison"]
    band_width = results["price_band"]
    fig, ax = plt.subplots(figsize=(11, 6))

    labels = []
    for start in comparison.index:
        labels.append(f"{start:,.0f}–{start + band_width:,.0f}")

    comparison.plot.bar(
        ax=ax, color=[EV_COLOR, CAR_COLOR], width=0.8, rot=25,
    )
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylim(0, comparison.max().max() * 1.3)
    ax.legend(title=None)
    ax.set_title("Stage 2: How Much Range Does Your Budget Buy?")
    ax.set_xlabel("Current Market Price Band (USD)")
    ax.set_ylabel("Median Nominal Range (km)")
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return fig

# Stage 4: Convenience

def plot_convenience(results):
    ranges = results["range_summary"]
    charging = results["charging_summary"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Range comparison
    comparison = ranges.pivot(
        index="body_type",
        columns="powertrain",
        values="median_range_km",
    )
    comparison = comparison.reindex(columns=["EV", "Conventional"])
    comparison = comparison.dropna(subset=["EV", "Conventional"])

    comparison.plot.bar(
        ax=axes[0], color=[EV_COLOR, CAR_COLOR], rot=25,
    )

    # Charging duration comparison
    charging_times = charging.pivot(
        index="body_type",
        columns="charging_mode",
        values="median_minutes",
    )
    charging_times = charging_times.rename(columns={
        "ac_minutes": "AC - Slower charging",
        "dc_minutes": "DC - Faster charging",
    })
    charging_times.plot.bar(
        ax=axes[1], rot=25,
        color={"AC - Slower charging": EV_COLOR, "DC - Faster charging": CAR_COLOR},
    )

    axes[0].set_title("Median Range")
    axes[0].set_xlabel("Car Type")
    axes[0].set_ylabel("Range (km)")

    axes[1].set_title("Median recorded EV charging duration")
    axes[1].set_xlabel("Car Type")
    axes[1].set_ylabel("Minutes")

    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)

    fig.suptitle("Stage 4: Convenience")
    fig.tight_layout()
    return fig

# Stage 6: Ownership Value

def plot_ownership(results):
    """Stage 6: observed retained value and purchase/current price medians."""
    age_comparison = results["age_comparison"]
    prices = results["price_comparison"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Retained value by age
    age_comparison.plot.bar(
        ax=axes[0], color=[EV_COLOR, CAR_COLOR], rot=0,
    )
    axes[0].set_ylim(0, age_comparison.max().max() * 1.15)
    axes[0].legend(title="Powertrain")

    # Original and current prices
    labels = ["EV\nOriginal", "EV\nCurrent", "Conventional\nOriginal", "Conventional\nCurrent"]
    amounts = [
        prices.loc["EV", "median_original_price"],
        prices.loc["EV", "median_current_price"],
        prices.loc["Conventional", "median_original_price"],
        prices.loc["Conventional", "median_current_price"],
    ]
    axes[1].bar(
        labels, amounts,
        color=[EV_COLOR, EV_COLOR, CAR_COLOR, CAR_COLOR], width=0.6,
    )
    axes[1].set_ylim(0, max(amounts) * 1.15)
    axes[1].ticklabel_format(axis="y", style="plain")

    axes[0].set_title("Median Retained Value by Vehicle Age")
    axes[0].set_xlabel("Vehicle Age Band (years, rounded down)")
    axes[0].set_ylabel("Median Current / Original Price (%)")

    axes[1].set_title("Median Original vs. Current Price")
    axes[1].set_xlabel("Powertrain and Price Type")
    axes[1].set_ylabel("Median Price (USD)")

    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)

    fig.suptitle("Stage 6: Ownership Value")
    fig.tight_layout()
    return fig


# Load the datasets, calculate each stage, then draw the charts.

def main():
    cars, _ = load_data()

    stage2 = value(
        cars, price_band=PRICE_BAND, body_type=BODY_TYPE,
    )
    stage4 = convenience(cars, body_type=BODY_TYPE)
    stage6 = ownership_verdict(cars, body_type=BODY_TYPE)

    plot_value(stage2)
    plot_convenience(stage4)
    plot_ownership(stage6)

    plt.show()


if __name__ == "__main__":
    main()
