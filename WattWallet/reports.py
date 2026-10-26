"""Dataset-only reports for stages 2, 4 and 6."""
import re
import numpy as np
import pandas as pd
from dataset import get_car_dataset_file_path, get_ev_market_dataset_file_path

def load_data():
    """Read through dataset.py; clean names and text cells without html imports."""
    frames = []
    for path in (get_car_dataset_file_path(), get_ev_market_dataset_file_path()):
        df = pd.read_csv(path)
        df.columns = [clean_column_name(c) for c in df.columns]
        for column in df.select_dtypes(include=["object", "string"]):
            df[column] = df[column].map(_clean_cell, na_action="ignore")
        frames.append(df)
    return tuple(frames)


def _clean_cell(value):
    """Remove pasted formatting and decode numeric character references."""
    value = str(value)
    def replace_reference(match):
        token = match.group(1)
        number = int(token[1:], 16) if token.lower().startswith("x") else int(token)
        return chr(number)
    value = re.sub(r"&#(x[0-9a-f]+|[0-9]+);", replace_reference, value, flags=re.I)
    return re.sub(r"\*+", "", value).strip()


def clean_column_name(column):
    """Convert spaces/punctuation to underscores and remove pasted formatting."""
    name = _clean_cell(str(column)).lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return name


def _number(df, column):
    """Invalid, missing or infinite numeric cells become NaN."""
    values = df[column].astype(str).str.replace(",", "", regex=False)
    return pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)


def _text(series):
    return series.fillna("").astype(str).str.strip().str.lower()


def _powertrains(cars):
    """Return BEV and non-hybrid ICE masks; unknown fuel labels are excluded."""
    truthy = ["true", "1", "1.0", "yes", "y"]
    fuel = _text(cars["fuel_type"])
    hybrid = (
        _text(cars["hybrid_flag"]).isin(truthy)
        | fuel.str.contains("hybrid")
        | _text(cars["hybrid_type"]).isin(
            ["hev", "phev", "mhev", "plug-in hybrid", "mild hybrid"]
        )
    )
    ev = (
        _text(cars["ev_flag"]).isin(truthy)
        | fuel.isin(["electric", "electricity", "bev", "battery electric"])
    ) & ~hybrid
    ice = fuel.isin(["gasoline", "petrol", "diesel", "gas", "cng", "lpg"])
    return ev, ice & ~hybrid & ~ev


def value(cars, *, price_band=50000, country=None, body_type=None,
          new_used_status=None, min_model_year=None, max_model_year=None):
    """Compare median nominal range by current-price band using the cars CSV."""

    vehicles = _prepare_cars(cars, country, body_type)

    if new_used_status is not None:
        status = _text(vehicles["new_used_status"])
        vehicles = vehicles[status == new_used_status.strip().lower()].copy()
    if min_model_year is not None:
        vehicles = vehicles[_number(vehicles, "model_year") >= min_model_year].copy()
    if max_model_year is not None:
        vehicles = vehicles[_number(vehicles, "model_year") <= max_model_year].copy()

    vehicles["comparison_price"] = _number(vehicles, "current_market_price")
    vehicles["range_km"] = np.nan
    ev_mask = vehicles["powertrain"] == "EV"
    car_mask = vehicles["powertrain"] == "Conventional"

    vehicles.loc[ev_mask, "range_km"] = _number(
        vehicles.loc[ev_mask], "electric_range_km"
    )
    tank = _number(vehicles.loc[car_mask], "fuel_tank_capacity_l")
    consumption = _number(vehicles.loc[car_mask], "fuel_consumption_highway_l_100km")
    tank = tank.where(tank > 0)
    consumption = consumption.where(consumption > 0)
    vehicles.loc[car_mask, "range_km"] = tank / consumption * 100

    vehicles = vehicles[
        (vehicles["comparison_price"] > 0) & (vehicles["range_km"] > 0)
    ].copy()
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


def _prepare_cars(cars, country=None, body_type=None):
    """Keep recognized battery EVs and conventional non-hybrid vehicles."""
    ev, ice = _powertrains(cars)
    df = cars.copy()
    df['powertrain'] = np.select([ev, ice], ['EV', 'Conventional'], default='Other')
    df = df.loc[df['powertrain'].ne('Other')].copy()
    if country is not None:
        df = df[_text(df["country"]) == country.strip().lower()].copy()
    if body_type is not None:
        df = df[_text(df["body_type"]) == body_type.strip().lower()].copy()
    return df


def convenience(cars, *, country=None, body_type=None):
    """Stage 4: recorded range and charging durations; no trip assumptions."""

    df = _prepare_cars(cars, country, body_type)
    ev_mask = df['powertrain'].eq('EV')
    electric_range = _number(df, 'electric_range_km').where(lambda s: s > 0)
    tank = _number(df, 'fuel_tank_capacity_l').where(lambda s: s > 0)
    consumption = _number(df, 'fuel_consumption_highway_l_100km').where(lambda s: s > 0)

    df['range_km'] = np.where(ev_mask, electric_range, tank / consumption * 100)
    range_rows = df.loc[df['range_km'].gt(0)].copy()
    range_summary = range_rows.groupby(['body_type', 'powertrain'], as_index=False).agg(
        median_range_km=('range_km', 'median'), observations=('range_km', 'count')
    )

    evs = df.loc[ev_mask].copy()
    evs['ac_minutes'] = _number(evs, 'ac_charging_time_hours').where(lambda s: s > 0) * 60
    supported = _text(evs['fast_charging_support']).isin(['true', '1', '1.0', 'yes', 'y'])
    evs['dc_minutes'] = _number(evs, 'dc_fast_charge_time_minutes').where(lambda s: s > 0).where(supported)
    
    durations = evs.melt(
        id_vars=['vehicle_id', 'make', 'model', 'body_type'],
        value_vars=['ac_minutes', 'dc_minutes'],
        var_name='charging_mode', value_name='reported_minutes',
    ).dropna(subset=['reported_minutes'])
    
    charging_summary = durations.groupby(['body_type', 'charging_mode'], as_index=False).agg(
        median_minutes=('reported_minutes', 'median'), observations=('reported_minutes', 'count')
    )

    return {'vehicles': df, 'range_summary': range_summary,
            'charging_observations': durations, 'charging_summary': charging_summary}


def ownership_verdict(cars, *, country=None, body_type=None):
    """Stage 6: median observed valuations, not future ownership costs."""
    vehicles = _prepare_cars(cars, country, body_type)
    vehicles["original_price"] = _number(vehicles, "original_price")
    vehicles["current_market_price"] = _number(vehicles, "current_market_price")
    vehicles["age_years"] = _number(vehicles, "vehicle_age")
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

    # Use the same shared-age observation population for the price panel.
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
