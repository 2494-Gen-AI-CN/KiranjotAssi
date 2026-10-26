"""Resolution hours and SLA breaches as NumPy arrays."""
import numpy as np
from desk import SLA_HOURS

def resolution_hours(desk):
    """Returns the hours each closed ticket took as an array"""
    hours = [] # empty python list
    
    # Loop through all the tickets - calculate the time for ticket 
    # resolution per ticket as a number (Not a timedelta)
    for t in desk:
        if t.status == "closed":
            hours.append((t.closed_at - t.opened_at).total_seconds() / 3600)
    
    return np.array(hours) # Based on the demo returns an nparray of floats, 
    # shape of [6,] (empty after comma is an implicit 1)
    
def sla_limits(desk):
    """Return the SLA hours of each closed ticket's own priority"""
    limits = [] # empty python list
    
    for t in desk:
        if t.status == "closed":
            limits.append(SLA_HOURS[t.priority])
    
    return np.array(limits) # shape of [3,], one dimensional 3 position np array

def breached(desk):
    """Return True for each closed ticket that took longer than it's SLA"""
    return resolution_hours(desk) > sla_limits(desk)

def summary(desk):
    """Return the mean, median, longest hour ticket, and breach count."""
    hours = resolution_hours(desk) # remember this returns an np.array
    
    return {
        "mean": float(hours.mean()),
        "median": float(np.median(hours)),
        "max": float(hours.max()),
        "breached": int(breached(desk).sum())
    }
    

        
    