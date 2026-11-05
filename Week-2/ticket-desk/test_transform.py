"""Tests for the warehouse transforms, with no database and no BigQuery."""
from datetime import date
from decimal import Decimal
import pytest
from transform import OPEN_END, apply_scd2

AS_OF = date(2026, 11, 5)

@pytest.fixture
def dimension():
    """Return a customer dimension of two current rows."""
    return [
        {"customer_key": 1, "customer_id": 1, "name": "Dana", "email": "dana@example.com",
         "country": "CA", "monthly_fee": Decimal("49.00"), "effective_from": date(2026, 10, 17),
         "effective_to": OPEN_END, "is_current": True},
        {"customer_key": 2, "customer_id": 2, "name": "Ravi", "email": "ravi@example.com",
         "country": "CA", "monthly_fee": Decimal("199.00"), "effective_from": date(2026, 10, 17),
         "effective_to": OPEN_END, "is_current": True},
    ]

def test_unchanged_source_keeps_dimension(dimension):
    """A source with the same tracked values changes no row."""
    assert apply_scd2(dimension, dimension, AS_OF) == dimension
 
def test_changed_fee_closes_old_row_and_adds_version(dimension):
    """A changed fee closes the current row and adds a new current version."""
    source = [dict(row) for row in dimension]
    source[0]["monthly_fee"] = Decimal("199.00")
    rows = apply_scd2(dimension, source, AS_OF)
    old, new = [row for row in rows if row["customer_id"] == 1]
    assert old["effective_to"] == AS_OF and not old["is_current"]
    assert new["effective_from"] == AS_OF and new["effective_to"] == OPEN_END
    assert new["customer_key"] == 3 and new["is_current"]

def test_rerun_after_change_adds_nothing(dimension):
    """Applying the same change a second time adds no row."""
    source = [dict(row) for row in dimension]
    source[0]["monthly_fee"] = Decimal("199.00")
    once = apply_scd2(dimension, source, AS_OF)
    assert apply_scd2(once, source, AS_OF) == once
