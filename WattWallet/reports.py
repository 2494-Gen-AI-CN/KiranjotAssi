import pandas as pd
import numpy as np
from dataset import get_car_dataset_file_path, get_ev_market_dataset_file_path

ev_dataset = pd.read_csv(get_ev_market_dataset_file_path())
car_dataset = pd.read_csv(get_car_dataset_file_path())

#Stage 1: purchase (K)
def purchase(car_dataset, ev_dataset):
    ev = ev_dataset[["brand", "model", "year", "price_usd"]]
    cars = car_dataset[["make", "model", "model_year", "original_price"]]

    comparisons = {}

    #Filtering out examples of similar vehicles in both datasets to plot
    ev_rows = ev[
        (ev["brand"] == "Tesla")
        & (ev["model"] == "Model Y")
        & (ev["year"] == 2022)
    ]
    car_rows = cars[
        (cars["make"].isin(["Toyota", "Honda", "Ford"]))
        & (cars["model"].isin(["RAV4", "CR-V", "Escape"]))
        & (cars["model_year"] == 2022)
    ]
    comparisons["Model Y"] = (ev_rows, car_rows)

    ev_rows = ev[
        (ev["brand"] == "Hyundai")
        & (ev["model"] == "Ioniq 5")
        & (ev["year"] == 2023)
    ]
    car_rows = cars[
        (cars["make"] == "Hyundai")
        & (cars["model"] == "Tucson")
        & (cars["model_year"] == 2023)
    ]
    comparisons["IONIQ 5"] = (ev_rows, car_rows)

    ev_rows = ev[
        (ev["brand"] == "Kia")
        & (ev["model"].isin(["EV6", "EV 6"]))
        & (ev["year"] == 2024)
    ]
    car_rows = cars[
        (cars["make"] == "Kia")
        & (cars["model"] == "Sportage")
        & (cars["model_year"] == 2024)
    ]
    comparisons["Kia EV6"] = (ev_rows, car_rows)

    ev_rows = ev[
        (ev["brand"] == "Volkswagen")
        & (ev["model"] == "ID.4")
        & (ev["year"] == 2025)
    ]
    car_rows = cars[
        (cars["make"] == "Volkswagen")
        & (cars["model"] == "Tiguan")
        & (cars["model_year"] == 2025)
    ]
    comparisons["Volkswagen ID.4"] = (ev_rows, car_rows)

    ev_rows = ev[
        (ev["brand"] == "Mercedes")
        & (ev["model"].isin(["EQE", "EQS"]))
        & (ev["year"] == 2024)
    ]
    car_rows = cars[
        (cars["make"] == "Mercedes-Benz")
        & (cars["model"].isin(["E-Class", "S-Class"]))
        & (cars["model_year"] == 2024)
    ]
    comparisons["Mercedes EQE/EQS"] = (ev_rows, car_rows)

    return comparisons

# stage 2: Value (A)
def value():
    """Explore how much extra range or performance you receive as your budget increases."""

    return None

# stage 3: Driving (K)
def driving(car_dataset, ev_dataset):
    """Estimate the distance needed for energy savings to recover the EV premium."""
    fuel_cost = 1.73
    electricity_cost = 0.166

    cars = car_dataset[
        ["make", "model", "model_year", "original_price",
         "fuel_consumption_combined_l_100km"]
    ]

    evs = ev_dataset[
        ["brand", "model", "year", "price_usd",
         "battery_capacity_kwh", "range_miles"]
    ]

    car = cars[
        (cars["make"] == "Mercedes-Benz")
        & (cars["model"] == "E-Class")
        & (cars["model_year"] == 2024)
    ]

    ev = evs[
        (evs["brand"] == "Mercedes")
        & (evs["model"] == "EQE")
        & (evs["year"] == 2024)
    ]

    if ev.empty or car.empty:
        raise ValueError("No matching EQE or E-Class rows found.")

    ev_price = ev["price_usd"].median()
    car_price = car["original_price"].median()

    # Estimate EV kWh per 100 km from battery capacity and range
    ev_kwh_per_100km = (
        ev["battery_capacity_kwh"] / ev["range_miles"] * 62.137
    ).median()

    car_l_per_100km = car["fuel_consumption_combined_l_100km"].median()

    ev_cost_per_km = ev_kwh_per_100km / 100 * electricity_cost
    car_cost_per_km = car_l_per_100km / 100 * fuel_cost

    savings_per_km = car_cost_per_km - ev_cost_per_km
    premium = ev_price - car_price

    break_even_km = premium / savings_per_km if savings_per_km > 0 else None

    return {
        "ev_price": ev_price,
        "car_price": car_price,
        "ev_cost_per_km": ev_cost_per_km,
        "car_cost_per_km": car_cost_per_km,
        "break_even_km": break_even_km,
    }

# stage 4: Convenience (A)
def convenience():
    """Compare trip spending and travel time, including charging stops and detours."""

    return None

# stage 5: Resale (K)
def resale(car_dataset):
    """Explore potential sale proceeds and how retained value affects long-term ownership costs."""
    car_dataset = car_dataset[["make", "model", "odometer_km", "model_year", "vehicle_age", "estimated_resale_value", "original_price"]]
    car_dataset = car_dataset[(car_dataset["make"].isin(["Hyundai"])) &
                              car_dataset["model"].isin(["Tucson", "Ioniq 5"]) &
                              car_dataset["model_year"].isin([2021])
                              ].dropna().copy()
    car_dataset["retained_value_percent"] = (
        car_dataset["estimated_resale_value"]
        / car_dataset["original_price"] * 100
    )
    car_dataset["depreciation_cost"] = (
        car_dataset["original_price"]
        - car_dataset["estimated_resale_value"]
    )
    return car_dataset

# stage 6: Ownership Verdict (A)
def ownership_verdict():
    """Combine purchase, running expenses, and resale into a five-year financial comparison."""

    return None