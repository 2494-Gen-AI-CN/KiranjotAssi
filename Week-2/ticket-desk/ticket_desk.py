"""Support-ticket desk: tickets, SLA deadlines and a board."""
import logging
from datetime import timedelta
from desk import NOW, Desk, Ticket, redact, ticket_refs
from storage import append_line, export_board, load_desk, save_desk
from stats import summary
from report import status_counts
from frame import load_frame
from chart import status_chart

log = logging.getLogger(__name__)

# Creating a constant for the file path to my json file
DATA = "tickets.json"

def main():
    """Load or seed the desk, print the board and save the tickets."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    
    # Using our JSON file
    try:
        desk = load_desk(DATA)
    except ValueError:
        log.error("Failed to read tickets.json")
        desk = Desk()
    
    
    # If my desk is empty (file didn't exist, or contained no tickets)
    # then use my old code to seed the desk
    if len(desk) == 0:
        t1 = Ticket(1, "Login page returns 500", "high", NOW - timedelta(hours=30))
        t2 = Ticket(2, "Invoice PDF is blank", "normal", NOW - timedelta(hours=50))
        t3 = Ticket(3, "Typo on pricing page", "normal", NOW - timedelta(hours=20))
        t4 = Ticket(4, "Checkout button frozen", "high", NOW - timedelta(hours=6))
        t5 = Ticket(5, "Export is missing rows", "normal", NOW - timedelta(hours=26))
        t6 = Ticket(6, "Add dark mode", "low", NOW - timedelta(hours=2))

        for t in [t1, t2, t3, t4, t5, t6]:
            desk.add(t)
        t1.close(t1.opened_at + timedelta(hours=3))
        t2.close(t2.opened_at + timedelta(hours=30))
        t3.close(t3.opened_at + timedelta(hours=10))
        t4.assign("Priya")
        t5.assign("Marco")
    
    # In python this is the syntax for handling exceptions: try-except
    try:
        # This contains the code that may generate an exception
        extra = Ticket(7, "Refund charged twice", "urgent", NOW)
    except ValueError as err: 
        # What to do if we trigger an exception in the try
        log.error("rejected ticket: %s", err)
    except KeyError as err: 
        # I don't know how we'd trigger this
        log.error('somehow got a key error')
    else: 
        # In python we can have an 'else' block - this triggers when the try 
        # DOESN'T generate an exception
        desk.add(extra)
    finally: 
        # regardless of if an exception was raised in the try, the presence of an else, etc
        # this code ALWAYS runs
        log.info("intake done")

    for t in desk:
        print(t.ticket_id, t.priority, t.status, t.days_open())
    late = desk.overdue()
    print(len(late))

    note = "Same problem as TD-2 and TD-5, reply to dana@example.com"
    print(ticket_refs(note))
    print(redact(note))
    
    # Intentionally creating a bad ticket - with a mis-set priority
    # t_bad = Ticket(1, "Login page returns 500", "High", NOW - timedelta(hours=30))
    
    export_board(desk, "board.txt")
    append_line("board.txt", "end of shift")
    
    # sleep(5)
    
    # delete_file("board.txt")
    
    # sleep(5)
    
    # delete_file("board.txt")
    
    save_desk(desk, DATA)

    print(summary(desk))
    
    print(status_counts(desk))

    df = load_frame(DATA)
    print(df[["ticket_id", "priority", "status"]])

    status_chart(df, "status.png")
    

if __name__ == "__main__":
    main()
