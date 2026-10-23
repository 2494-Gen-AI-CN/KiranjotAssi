import pandas as pd
import numpy as np
from dataset import get_car_dataset_file_path, get_ev_market_dataset_file_path

ev_dataset = pd.read_csv(get_ev_market_dataset_file_path)
car_dataset = pd.read_csv(get_car_dataset_file_path)

ev_dataset.head(10)


# stage 1: Purchase (K)
def purchase():
    """Compare similar EVs and conventional cars to reveal the upfront price difference."""

    return None

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