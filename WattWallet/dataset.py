from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "datasets"

# specifiy the file path respectively 
def get_car_dataset_file_path():
    return DATA_DIR / "vehicle_comparison_all_cars.csv"


def get_ev_market_dataset_file_path():
    return DATA_DIR / "ev_market_2026.csv"
