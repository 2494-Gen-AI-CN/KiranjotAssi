import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from reports import resale, driving, purchase
from dataset import get_car_dataset_file_path, get_ev_market_dataset_file_path

ev_dataset = pd.read_csv(get_ev_market_dataset_file_path())
car_dataset = pd.read_csv(get_car_dataset_file_path())

#Stage 1: Purchase comparison (K)
def plot_purchase_comparison(comparisons):
    labels, ev_medians, car_medians = [], [], []

    for label, (ev_rows, car_rows) in comparisons.items():
        if ev_rows.empty or car_rows.empty:
            print(f"Skipping {label}: no matchhing rows in one dataset")
            continue
        labels.append(label)
        ev_medians.append(ev_rows["price_usd"].median())
        car_medians.append(car_rows["original_price"].median())

    x = np.arange(len(labels))
    width = 0.38

    fig,ax = plt.subplots(figsize=(11,6))
    ax.bar(x-width/2,ev_medians, width, label="EV Price")
    ax.bar(x-width/2, car_medians, width, label="Conventional car Price")

    ax.set_xticks(x,labels, rotation=20, ha="right")
    ax.set_ylabel("Median recorded price")
    ax.set_title("EV and Conventional Vehicle Prices by Comparison")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()
    for label, (ev_rows, car_rows) in comparisons.items():
        print(f"{label}: EV rows={len(ev_rows)}, conventional rows={len(car_rows)}")

def plot_driving_comparison(car_dataset, ev_dataset):
    result = driving(car_dataset, ev_dataset)

    if result["break_even_km"] is None:
        print("THE EV doesn't save money on energy under these assumptions")
        return
    distance = np.linspace(
        0, max(result["break_even_km"]*1.25, 1000), 200
    )

    ev_total = result["ev_price"] + distance * result["ev_cost_per_km"]
    car_total = result["car_price"] + distance * result["car_cost_per_km"]

    plt.figure(figsize=(9,5))
    plt.plot(distance, ev_total, label="EQE: purchase + electricity")
    plt.plot(distance, car_total, label="E-Class: purchase + gasoline")
    plt.axvline(
        result["break_even_km"],
        color="gray",
        linestyle="--",
        label=f"Break-even: {result['break_even_km']:,.0f} km"
    )

    plt.xlabel("Distance Driven (KM)")
    plt.ylabel("Total cost (CAD)")
    plt.title("2024 Mercedes EQE vs E-Class")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_driving_comparison(car_dataset, ev_dataset)
comparisons = purchase(car_dataset,ev_dataset)
plot_purchase_comparison(comparisons)