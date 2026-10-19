import math
from datetime import datetime, timedelta
import logging 
import re
from desk import NOW, Desk

SLA_HOURS = {"high": 4, "normal": 24, "low": 72}
NOW = datetime(2026, 10, 19, 14, 0)
TICKET_REF = re.compile(r"\bTD-(\d+)\b") #matches my ticket format
EMAIL = re.compile(r"[\w.+-]+@[\w-]+.\[\w.]+")

#adding my logger
log = logging.getLogger(__name__) #__name__ describes the module

logging.basicConfig(level=logging.WARNING, format ="%(levelname)s %(name)s: %(message)s")

class Ticket:
    def __init__(self, ticket_id, title, priority, opened_at = datetime.now ):
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

    for t in tickets:
        print(t.ticket_id, t.priority, t.status, t.days_open())
        desk.add(t) #Add ticket to my desk


if __name__ =="__main__":
    main()


