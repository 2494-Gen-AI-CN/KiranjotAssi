import pandas as pd
import numpy as np
from dataset import get_car_dataset_file_path, get_ev_market_dataset_file_path

ev_dataset = pd.read_csv(get_ev_market_dataset_file_path())
car_dataset = pd.read_csv(get_car_dataset_file_path())


# stage 1: Purchase (K)
def purchase(car_dataset, ev_dataset):
    """Compare similar EVs and conventional cars to reveal the upfront price difference."""
    cleaned_ev_dataset = ev_dataset[["brand", "model", "year", "price_usd"]]
    cleaned_car_dataset = car_dataset[["make", "model", "model_year", "original_price"]]
    # Compare conventional cars with EV cars
    #this one compares Tesla Model Y with Toyota RAV4, Honda CR-V, Ford Escape
    tesla_value_comparsion = cleaned_ev_dataset[
        (cleaned_ev_dataset["brand"] == "Tesla") & 
        (cleaned_ev_dataset["model"] == "Model Y") & 
        (cleaned_ev_dataset["year"] == 2022)
        ]
    model_y_comparision = cleaned_car_dataset[
        (cleaned_car_dataset["make"].isin(["Toyota", "Honda", "Ford"])) & 
        (cleaned_car_dataset["model"].isin(["RAV4", "CR-V", "Escape"]))&
        (cleaned_car_dataset["model_year"].isin([2022]))
        ]

    #This example compares Hyundai Ioniq 5 with Hyundai Tucson
    ioniq5_value_comparsion = cleaned_ev_dataset[
        (cleaned_ev_dataset["brand"] == "Hyundai") & 
        (cleaned_ev_dataset["model"] == "Ioniq 5") &
        (cleaned_ev_dataset["year"] == 2023)
        ]
    hyundai_tucson_comparision = cleaned_car_dataset[
        (cleaned_car_dataset["make"].isin(["Hyundai"])) & 
        (cleaned_car_dataset["model"].isin(["Tucson"])) &
        (cleaned_car_dataset["model_year"].isin([2023]))
        ]

    #This example compares Kia EV6 with Kia Sportage
    ev6_value_comparsion = cleaned_ev_dataset[
        (cleaned_ev_dataset["brand"] == "Kia") & 
        (cleaned_ev_dataset["model"] == "EV 6") &
        (cleaned_ev_dataset["year"] == 2024)
        ]
    kia_sportage_comparision = cleaned_car_dataset[
        (cleaned_car_dataset["make"].isin(["Kia"])) & 
        (cleaned_car_dataset["model"].isin(["Sportage"])) &
        (cleaned_car_dataset["model_year"].isin([2024]))
        ]

    #This example compares Volkswagen id4 with Volkswagen Tiguan
    id4_value_comparsion = cleaned_ev_dataset[
        (cleaned_ev_dataset["brand"] == "Volkswagen") & 
        (cleaned_ev_dataset["model"] == "ID.4") &
        (cleaned_ev_dataset["year"] == 2025)
        ]
    tiguan_comparision = cleaned_car_dataset[
        (cleaned_car_dataset["make"].isin(["Volkswagen"])) & 
        (cleaned_car_dataset["model"].isin(["Tiguan"])) & 
        (cleaned_car_dataset["model_year"].isin([2025]))
        ]

    #This example compares Mercedes EQE/EQS with Mercedes e-class/s-class
    eqe_eqs_value_comparsion = cleaned_ev_dataset[
        (cleaned_ev_dataset["brand"] == "Mercedes") & 
        (cleaned_ev_dataset["model"].isin(["EQE", "EQS"])) & 
        (cleaned_ev_dataset["year"].isin([2024]))
        ]
    sclass_cclass_comparision = cleaned_car_dataset[
        (cleaned_car_dataset["make"].isin(["Mercedes-Benz"])) & 
        (cleaned_car_dataset["model"].isin(["C-Class", "S-Class"])) & 
        (cleaned_car_dataset["model_year"].isin([2024]))
        ]
    print(eqe_eqs_value_comparsion)
    print(sclass_cclass_comparision)
    return None

purchase(car_dataset, ev_dataset)
# stage 2: Vlaue (A)
def value():
    """Explore how much extra range or performance you receive as your budget increases."""

    return None

# stage 3: Driving (K)
def driving():
    """Estimate the driving distance needed for energy savings to recover the EV’s upfront premium."""

    return None

# stage 4: Convenience (A)
def convenience():
    """Compare trip spending and travel time, including charging stops and detours."""

    return None

# stage 5: Resale (K)
def resale():
    """Explore potential sale proceeds and how retained value affects long-term ownership costs."""

    return None

# stage 6: Ownership Verdict (A)
def ownership_verdict():
    """Combine purchase, running expenses, and resale into a five-year financial comparison."""

    return None