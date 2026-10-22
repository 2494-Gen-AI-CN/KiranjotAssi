"""Load the desk's tickets into a pandas table (dataframe)"""
import pandas as pd

def load_frame(path):
    """Return the tickets in tickets.json as a Dataframe with datetime columns"""
    df = pd.read_json(path) # "tickets.json"
    
    # By default Pandas is going to try to give your columns an appropriate 
    # data type. For things like datetime - they'll be read in as strings. 
    # We can easily nudge Pandas to change the type.
    df["opened_at"] = pd.to_datetime(df["opened_at"])
    df["closed_at"] = pd.to_datetime(df["closed_at"])

    #deriving a new column for our dataframe from existing data. "hours" is not a field in the JSON
    df["hours"] = (df["closed_at"] - df["opened_at"]).dt.total_seconds() /3600
    return df

def status_table(df):
    """Return how many tickets belong to each status"""
    return df["status"].value_counts()

def hours_by_priority(df):
    """Return the mean hours to resolve for each priority"""
    return df.groupby("priority")["hours"].mean()
