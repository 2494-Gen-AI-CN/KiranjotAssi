"""Dataset reports for stages 2, 4 and 6. No text or header cleaning."""
import numpy as np
import pandas as pd
from dataset import get_car_dataset_file_path, get_ev_market_dataset_file_path


def load_data():
    """Read both CSVs as supplied, without modifying their text or headers."""
    cars = pd.read_csv(get_car_dataset_file_path())
    evs = pd.read_csv(get_ev_market_dataset_file_path())
    return cars, evs


def _prepare_cars(cars, country=None, body_type=None):
    """Select recognized battery EVs and non-hybrid conventional cars."""
    vehicles = cars.dropna(subset=[
        "country", "body_type", "fuel_type", "ev_flag", "hybrid_flag",
    ]).copy()

    non_hybrid = vehicles["hybrid_flag"] == 0
    ev_mask = (vehicles["ev_flag"] == 1) & non_hybrid
    car_mask = (
        (vehicles["ev_flag"] == 0)
        & non_hybrid
        & vehicles["fuel_type"].isin(["Petrol", "Gasoline", "Diesel", "Gas", "CNG", "LPG"])
    )
    vehicles["powertrain"] = np.select(
        [ev_mask, car_mask], ["EV", "Conventional"], default="Other"
    )
    vehicles = vehicles[vehicles["powertrain"] != "Other"].copy()

    if country is not None:
        vehicles = vehicles[vehicles["country"] == country].copy()
    if body_type is not None:
        vehicles = vehicles[vehicles["body_type"] == body_type].copy()
    return vehicles


def _range_data(vehicles):
    evs = vehicles[vehicles["powertrain"] == "EV"].copy()
    evs["range_km"] = evs["electric_range_km"]
    evs = evs.dropna(subset=["range_km"])
    evs = evs[evs["range_km"] > 0].copy()

    cars = vehicles[vehicles["powertrain"] == "Conventional"].copy()
    cars = cars.dropna(subset=[
        "fuel_tank_capacity_l", "fuel_consumption_highway_l_100km",
    ])
    cars = cars[
        (cars["fuel_tank_capacity_l"] > 0)
        & (cars["fuel_consumption_highway_l_100km"] > 0)
    ].copy()
    cars["range_km"] = (
        cars["fuel_tank_capacity_l"]
        / cars["fuel_consumption_highway_l_100km"] * 100
    )
    return pd.concat([evs, cars]).sort_index()


# Stage 2: Value Check

def value(cars, *, price_band=50000, country=None, body_type=None,
          new_used_status=None, min_model_year=None, max_model_year=None):
    """Compare median range within current-price bands shared by both groups."""
    vehicles = _prepare_cars(cars, country, body_type)

    vehicles["comparison_price"] = vehicles["current_market_price"]
    vehicles = vehicles.dropna(subset=["comparison_price"])
    vehicles = vehicles[vehicles["comparison_price"] > 0].copy()
    vehicles = _range_data(vehicles)
    vehicles["price_band_start"] = (
        np.floor(vehicles["comparison_price"] / price_band) * price_band
    )
    summary = vehicles.groupby(
        ["price_band_start", "powertrain"], as_index=False
    ).agg(
        median_range=("range_km", "median"),
        observations=("range_km", "size"),
    )
    comparison = summary.pivot(
        index="price_band_start", columns="powertrain", values="median_range"
    )
    comparison = comparison.reindex(columns=["EV", "Conventional"])
    comparison = comparison.dropna(subset=["EV", "Conventional"])
    counts = summary.pivot(
        index="price_band_start", columns="powertrain", values="observations"
    )
    counts = counts.reindex(index=comparison.index, columns=["EV", "Conventional"])
    return {
        "vehicles": vehicles,
        "range_comparison": comparison,
        "observation_counts": counts,
        "price_band": price_band,
    }


# Stage 4: Convenience

def convenience(cars, *, country=None, body_type=None):
    """Compare nominal ranges and recorded charging durations, not trip delays. """
    vehicles = _prepare_cars(cars, country, body_type)
    vehicles = _range_data(vehicles)
    evs = vehicles[vehicles["powertrain"] == "EV"].copy()
    conventional = vehicles[vehicles["powertrain"] == "Conventional"].copy()

    evs = evs.dropna(subset=["vehicle_id", "make", "model", "fast_charging_support"])
    evs["ac_minutes"] = evs["ac_charging_time_hours"] * 60
    evs["dc_minutes"] = evs["dc_fast_charge_time_minutes"]
    evs = evs.dropna(subset=["ac_minutes"])
    evs = evs[evs["ac_minutes"] > 0].copy()

    # The supplied sample mixes 0/1 with the literal text "False".
    evs["fast_charging_support"] = evs["fast_charging_support"].replace(
        {"False": 0, "True": 1}
    )
    evs["fast_charging_support"] = pd.to_numeric(
        evs["fast_charging_support"], errors="coerce"
    )
    evs = evs.dropna(subset=["fast_charging_support"])
    supported = evs["fast_charging_support"] == 1
    not_supported = evs["fast_charging_support"] == 0
    # Missing DC time excludes a supported EV's entire row. DC is not required
    # for EVs whose flag explicitly says fast charging is unsupported.
    evs = evs[not_supported | (supported & (evs["dc_minutes"] > 0))].copy()
    supported = evs["fast_charging_support"] == 1
    evs.loc[~supported, "dc_minutes"] = np.nan

    complete = pd.concat([evs, conventional]).sort_index()
    range_summary = complete.groupby(
        ["body_type", "powertrain"], as_index=False
    ).agg(
        median_range_km=("range_km", "median"),
        observations=("range_km", "count"),
    )
    durations = evs.melt(
        id_vars=["vehicle_id", "make", "model", "body_type"],
        value_vars=["ac_minutes", "dc_minutes"],
        var_name="charging_mode", value_name="reported_minutes",
    )
    durations = durations.dropna(subset=["reported_minutes"])
    charging_summary = durations.groupby(
        ["body_type", "charging_mode"], as_index=False
    ).agg(
        median_minutes=("reported_minutes", "median"),
        observations=("reported_minutes", "count"),
    )
    return {
        "vehicles": complete,
        "range_summary": range_summary,
        "charging_observations": durations,
        "charging_summary": charging_summary,
    }


# Stage 6: Ownership Value

def ownership_verdict(cars, *, country=None, body_type=None):
    """Compare recorded valuations, not future resale or total ownership cost."""
    vehicles = _prepare_cars(cars, country, body_type)
    vehicles = vehicles.dropna(subset=["vehicle_id"])
    vehicles["age_years"] = vehicles["vehicle_age"]
    vehicles = vehicles.dropna(subset=[
        "original_price", "current_market_price", "age_years",
    ])
    vehicles = vehicles[
        (vehicles["original_price"] > 0)
        & (vehicles["current_market_price"] > 0)
        & (vehicles["age_years"] >= 0)
    ].copy()
    vehicles["age_band"] = np.floor(vehicles["age_years"]).astype(int)
    vehicles["price_change"] = vehicles["original_price"] - vehicles["current_market_price"]
    vehicles["retained_percent"] = (
        vehicles["current_market_price"] / vehicles["original_price"] * 100
    )
    age_summary = vehicles.groupby(
        ["age_band", "powertrain"], as_index=False
    ).agg(
        median_retained_percent=("retained_percent", "median"),
        observations=("retained_percent", "count"),
    )
    age_comparison = age_summary.pivot(
        index="age_band", columns="powertrain", values="median_retained_percent"
    )
    age_comparison = age_comparison.reindex(columns=["EV", "Conventional"])
    age_comparison = age_comparison.dropna(subset=["EV", "Conventional"])
    compared = vehicles[vehicles["age_band"].isin(age_comparison.index)].copy()
    price_comparison = compared.groupby("powertrain").agg(
        median_original_price=("original_price", "median"),
        median_current_price=("current_market_price", "median"),
        observations=("vehicle_id", "size"),
    )
    price_comparison = price_comparison.reindex(["EV", "Conventional"])
    price_comparison = price_comparison.dropna(
        subset=["median_original_price", "median_current_price"]
    )
    return {
        "vehicles": vehicles,
        "compared_vehicles": compared,
        "age_summary": age_summary,
        "age_comparison": age_comparison,
        "price_comparison": price_comparison,
    }
