"""Tests for the warehouse transforms, with no database and no BigQuery."""
from datetime import date, datetime

from decimal import Decimal
import pandas as pd
import pytest
from transform import OPEN_END, apply_scd2, clean_events

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

@pytest.fixture
def staged():
    """Return four staged events out of id order, and the open times of tickets 4 and 6."""
    events = pd.DataFrame({
        "event_id": [2, 1, 3, 4],
        "ticket_id": [4, 4, 2, 6],
        "kind": ["assigned", "assigned", "closd", "assigned"],
        "note": ["copy", "good", "typo", "early"],
        "created_at": [datetime(2026, 10, 19, 9), datetime(2026, 10, 19, 9),
                       datetime(2026, 10, 18, 18), datetime(2026, 10, 19, 11)],
    })
    tickets = pd.DataFrame({
        "ticket_id": [4, 6],
        "opened_at": [datetime(2026, 10, 19, 8), datetime(2026, 10, 19, 12)],
    })
    return events, tickets

def test_clean_keeps_good_rows(staged):
    """Only the good event comes out clean, in the five event columns."""
    clean = clean_events(*staged)[0]
    assert list(clean["event_id"]) == [1]
    assert list(clean.columns) == ["event_id", "ticket_id", "kind", "note", "created_at"]

def test_clean_rejects_each_bad_row_with_its_reason(staged):
    """Each bad event is rejected once, with the rule it broke."""
    rejects = clean_events(*staged)[1]
    assert list(rejects["event_id"]) == [2, 3, 4]
    assert list(rejects["reason"]) == ["duplicate", "unknown kind", "before ticket opened"]

def test_clean_keeps_first_copy_of_a_duplicate(staged):
    """Of two copies listed out of order, the one with the higher event_id is rejected."""
    rejects = clean_events(*staged)[1]
    assert list(rejects[rejects["reason"] == "duplicate"]["event_id"]) == [2]









