"""Supporting Ticket Desk"""
import logging
import re
import math
from datetime import datetime, timedelta

SLA_HOURS = {"high": 4, "normal": 24, "low": 72}
NOW = datetime(2026, 10, 19, 14, 0)

TICKET_REF = re.compile(r"\bTD-(\d+)\b") #matches my ticket format
EMAIL = re.compile(r"[\w.+-]+@[\w-]+.\[\w.]+")

#adding my logger
log = logging.getLogger(__name__) #__name__ describes the module

logging.basicConfig(level=logging.WARNING, format ="%(levelname)s %(name)s: %(message)s")

class Desk:
    def __init__(self):
        self.tickets = []

    def add(self, ticket):
        self.tickets.append(ticket)
        log.info("added %s", ticket)

    def __len__(self):
        return len(self.tickets)
    #If i want to be able to easily iterate over something - I have to use this
    #this is used in for loops, and without this, I can't do for things in collection do y 
    def __iter__(self):
        return iter(self.tickets)

    def overdue(self, now=NOW):
        """this method gives me all tickets assigned to the desk that are overdue"""

        late = []
        for t in self.tickets:
            if t.status != "closed" and now > t.deadline():
                log.warning("%s is past its SLA", t)
                late.append(t)

        return late    

    def ticket_refs(text):
        refs = []
        for match in TICKET_REF.finditer(text):
            refs.append(int(match.group(1)))  
        return refs
