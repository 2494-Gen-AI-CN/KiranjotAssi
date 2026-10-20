import math
from datetime import datetime, timedelta
import logging 
import re
from desk import NOW, Desk
from storage import append_line, export_board, read_lines, delete_file
import time

SLA_HOURS = {"high": 4, "normal": 24, "low": 72}
NOW = datetime(2026, 10, 19, 14, 0)
TICKET_REF = re.compile(r"\bTD-(\d+)\b") #matches my ticket format
EMAIL = re.compile(r"[\w.+-]+@[\w-]+.\[\w.]+")

#adding my logger
log = logging.getLogger(__name__) #__name__ describes the module

logging.basicConfig(level=logging.WARNING, format ="%(levelname)s %(name)s: %(message)s")

class Ticket:
    def __init__(self, ticket_id, title, priority, opened_at = datetime.now ):
        if priority not in SLA_HOURS:
            #Try to use the built in errors, otherwise you can use the error base class to format your own
            raise ValueError(f"unknown priority: {priority!r}") #the !r will print 'wrong' instead of wrong without the quotes
        self.ticket_id = ticket_id
        self.title = title
        self.priority = priority
        self.opened_at = opened_at #If we use a double underscore, we get a private field/property. This is sort-of enforced
        self.assignee = None #underscore on a property denotes "protected", intended for internal or sublass use only
        self.is_open = True
        self.closed_at = None

    def deadline(self):
        return self.__opened_at + timedelta(hours=SLA_HOURS[self.priority])

    def days_open(self, now = NOW):
        hours = (now-self.opened_at).total_seconds() /3600
        return math.ceil(hours/24) #using ceil() from math module
    
    def assign(self, agent):
        self._assignee = agent
        self.status = "assign"
        log.info("%s assigned to %s", self, agent)       

    def close(self, at):
        self.status = "closed"
        self.closed_at = at  
        log.info("%s closed", self)

    def __repr__(self):
        return f"TD-{self.ticket_id} {self.title} [{self.priority}, {self.status}]"
    

# virtual environment - you might have conflicts within versions. It is difficult to clean up
# make a virtual environment, and have the installs from pip go in each virtual environment, and then you won't get collisions

# Use this line: py -3.15 -m venv .venv
# Always remember to turn it on using source .venv/Scripts/Activate


#pylint errors: c is convention, w is warning, r is refactor, e is error


def main():
    """This Method will act as the entrypoint of my application"""
    t1 = Ticket(1, "Login Page returns 500", "high", NOW - timedelta(hours = 30))
    t2 = Ticket(2, "Invoice PDF is blank", "normal", NOW - timedelta(hours = 50))
    t4 = Ticket(3, "Add dark mode", "low", NOW - timedelta(hours = 26))
    t3 = Ticket(4, "Typo on pricing page", "normal", NOW - timedelta(hours = 20))

    tickets = [t1, t1, t3, t4]

    t1.close(t1.opened_at + timedelta(hours = 3))
    t3.close(t3.opened_at + timedelta(hours = 10))

    t2.assign("Marco")
    t4.assign("Jonathan")

    desk = Desk()

    try: 
        #this contains the code that may generate an exception
        extra = Ticket(7, "Refund charged twice", "urgent", NOW)
    except ValueError as err:
        #What to do if we trigger an exception
        log.error("rejected ticket: %s", err)
    except KeyError as err:
        log.error("somehow got a key error")
    else:
        # in Python, we can add an else block - this triggers when the try 
        # doesn't generate an exception
        desk.add(extra)
    finally: 
        # regardless of if an exception was raised in the try, the presence of an else, wtc.
        # this code always runs
        log.info("intake done")

    for t in tickets:
        print(t.ticket_id, t.priority, t.status, t.days_open())
        desk.add(t) #Add ticket to my desk

#Intentionally create a bad ticket
#t_bad = Ticket(1, "Login Page returns 500", "High", NOW - timedelta(hours = 30))

    export_board(desk, "board.txt")
    append_line("board.txt", "end of shift")

    time.sleep(5)

    delete_file("board.txt")

if __name__ =="__main__":
    main()


