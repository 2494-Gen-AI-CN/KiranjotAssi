"""Transform the desks rows before they go into the warehouse"""
from datetime import date

OPEN_END = date(9999, 12, 31)
TRACKED = ("name", "email", "country", "monthly_fee")

def apply_scd2(dimension, source, as_of):
    """Return the customer dimension with type 2 history applied on as_of"""
    rows = [dict(row) for row in dimension]
    current = {row["customer_id"]: row for row in rows if row["is_current"]}
    next_key = max((row["customer_key"] for row in rows), default=0) +1 
    for src in source:
        old = current.get(src["customer_id"])
        if old is not None:
            if all(old[col] == src[col] for col in TRACKED):
                continue
            old["effective_to"] = as_of
            old["is_current"] = False
        rows.append(dict(src, customer_key=next_key, effective_from=as_of,
                         effective_to=OPEN_END, is_current=True))
        next_key+=1
    return rows
