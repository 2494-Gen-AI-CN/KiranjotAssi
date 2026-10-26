from datetime import datetime, timedelta
import pytest 
from desk import NOW, Desk, Ticket, redact, ticket_refs
from storage import load_desk, save_desk
import numpy as np
from stats import breached, resolution_hours, summary
from report import rows, status_counts, work_queue


"""This file contains tests for Desk object stuff"""

# Inside a test file (who's name starts with "test_", our methods also start with)
# our methods also start with "test_"
def test_high_priority_deadline_is_four_hours():
    # Arrange (sometimes not needed)
    # Create any needed sample data to pass into the test
    opened = datetime(2026, 10, 19, 8, 0)
    ticket = Ticket(1, "Login page returns 500", "high", opened)

    # Act
    # Call the code that is under test 
    
    # Assert 
    # Assert something about the outcome of a method - this is what defines
    # pass or fail for your test. It is common for smaller tests to have act + assert
    # on the same line
    assert ticket.deadline() == opened + timedelta(hours=4)

# We can test for things like exceptions being raised if we give 
# bad input. 
def test_unknown_priority_raises_value_error():
    with pytest.raises(ValueError, match="urgent"):
        Ticket(1, "Login page returns 500", "urgent", NOW)
        
# Testing the rule that closed tickets are not considered overdue 
# (based on our very simple business logic)
def test_overdue_skips_closed_tickets():
    
    # Arrange
    desk = Desk()
    opened = NOW - timedelta(hours=100)
    done = Ticket(1, "Invoice PDF is blank", "high", opened)
    late = Ticket(2, "Checkout button frozen", "high", opened)
    desk.add(done) 
    desk.add(late)
    done.close(opened + timedelta(hours=2)) # Our done ticket is closed 2 hours after opening
    
    # Act + Assert
    assert desk.overdue() == [late]
    
def test_redact_hides_email():
    # This test is so simple, I don't have to arrange. It all happens 
    # in the assert
    assert redact("write to ana@example.com now") == "write to [email] now"
    
def test_ticket_refs_reads_numbers():
    assert ticket_refs("Same problem as TD-2 and TD-5") == [2, 5]
    
    
# A fixture is a function that builds test data. Two tests that need the same object,
# in our case, maybe the same ticket or desk created the exact same way shouldn't
# need to build them by hand each time. The fixture JUST returns test data. It is
# NOT a test - it does not run as a test. 

# Pytest will call the fixture function FOR EACH test. This means each test can modify
# it's fixtures (during an act or assert for example) and the next test gets a fresh one
@pytest.fixture
def sample_desk():
    # code for generating a desk (with a variety tickets)
    desk = Desk()
    opened = datetime(2026, 10, 18, 8, 0)
    fast = Ticket(1, "Login page returns 500", "high", opened)
    slow = Ticket(2, "Invoice PDF is blank", "normal", opened)
    busy = Ticket(3, "Checkout button frozen", "high", opened)
    fresh = Ticket(4, "Add dark mode", "low", opened)
    
    for ticket in [fast, slow, busy, fresh]:
        desk.add(ticket)
    
    fast.close(opened + timedelta(hours=3))
    slow.close(opened + timedelta(hours=30))
    
    busy.assign("Priya")
    return desk

# Lets add some tests that use my fixture
# tmp_path is a built in fixture - spits out a temporary directory for file_IO testing
# so common, they built it into pytest
# we pass fixtures as arguments - ask for the name of the fixture function, pytest will 
# call it for you and allow the test to use it's output
def test_save_then_load_keeps_every_ticket(tmp_path, sample_desk):
    # Arrange
    path = tmp_path / "tickets.json" # some/dir/name/tickets.json
    
    # Act - calling the method under test (save_desk() from desk.py)
    save_desk(sample_desk, path)
    loaded_desk = load_desk(path)
    
    # Assert
    assert len(loaded_desk) == len(sample_desk)
    assert repr(loaded_desk.tickets) == repr(sample_desk.tickets)
    assert loaded_desk.tickets[1].closed_at == sample_desk.tickets[1].closed_at

def test_missing_file_gives_empty_desk(tmp_path):
    assert len(load_desk(tmp_path / "nothing.json")) == 0
    
def test_corrupt_file_raises_value_error(tmp_path):
    path = tmp_path / "tickets.json"
    
    path.write_text("[{", encoding="utf-8")
    
    with pytest.raises(ValueError, match="not valid JSON"):
        load_desk(path)
        
@pytest.mark.parametrize("priority, hours", [("high", 4), ("normal", 24), ("low", 72)])
def test_sla_hours(priority, hours):
    ticket = Ticket(1, "Any title", priority, NOW)
    assert ticket.deadline() - NOW == timedelta(hours=hours)

def test_hours_array_float(sample_desk):
    # We think intuitively that when we do a comparison of two np.arrays
    # we are comparing the entire array and getting back one True or False
    # What we're actually getting back is [True, True] 
    # assert resolution_hours(sample_desk) == [3.0, 30.0]
    hours = resolution_hours(sample_desk)
    assert hours.dtype == np.float64 # correct data type
    assert hours.shape == (2,) # asserting we should have a 2 position 1-d array
    
    # This is for demo/curiosity only 
    # npt.assert_allclose(hours, sample_desk, rtol=1e-7)
    
    # assert np.array_equal(hours, sample_desk) # see if the arrays are the same shape,
    # as well as the same contents

def test_breach_mask(sample_desk):
    assert np.array_equal(breached(sample_desk), [False, True])    

def test_summary_mean(sample_desk):
    assert summary(sample_desk)["mean"] == pytest.approx(16.5)
    
def test_status_counts(sample_desk):
    assert status_counts(sample_desk) == {"closed": 2, "assigned": 1, "open": 1}
    
def test_rows_are_named(sample_desk):
    """Rows are read by field name; an open ticket has no hours."""
    table = rows(sample_desk)
    assert table[0].status == "closed"
    assert table[0].hours == 3.0
    assert table[3].hours is None
    
def test_work_queue_puts_soonest_first(sample_desk):
    """The queue holds unfinished tickets, soonest deadline first."""
    sample_desk.tickets.reverse()
    queue = work_queue(sample_desk)
    assert list(queue) == [3, 4]