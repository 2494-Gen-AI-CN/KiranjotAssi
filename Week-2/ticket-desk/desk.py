"""The desk model: tickets, SLA rules and text patterns."""
import logging
import math
import re
from datetime import datetime, timedelta

SLA_HOURS = {"high": 4, "normal": 24, "low": 72}
NOW = datetime(2026, 10, 19, 14, 0)
TICKET_REF = re.compile(r"\bTD-(\d+)\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
log = logging.getLogger(__name__)


class Ticket:
    """A support ticket with a priority, a status and an SLA deadline."""
    def __init__(self, ticket_id, title, priority, opened_at):
        
        if priority not in SLA_HOURS:
            raise ValueError(f"unknown priority: {priority!r}") # this will print 'wrong' instead of just wrong 
        
        self.ticket_id = ticket_id
        self.title = title
        self.priority = priority
        self.opened_at = opened_at
        self.status = "open"
        self.assignee = None
        self.closed_at = None

    def __repr__(self):
        return f"TD-{self.ticket_id} {self.title} [{self.priority}, {self.status}]"

    def deadline(self):
        """Return the moment this ticket's SLA runs out."""
        return self.opened_at + timedelta(hours=SLA_HOURS[self.priority])

    def days_open(self, now=NOW):
        """Return whole days open, counting a part day as a full day."""
        hours = (now - self.opened_at).total_seconds() / 3600
        return math.ceil(hours / 24)

    def assign(self, agent):
        """Give the ticket to an agent and mark it assigned."""
        self.assignee = agent
        self.status = "assigned"
        log.info("%s assigned to %s", self, agent)

    def close(self, at):
        """Mark the ticket closed at the given moment."""
        self.status = "closed"
        self.closed_at = at
        log.info("%s closed", self)


class Desk:
    """The collection of tickets the team works from."""
    def __init__(self):
        self.tickets = []

    def add(self, ticket):
        """Add a ticket to the desk and log it."""
        self.tickets.append(ticket)
        log.info("added %s", ticket)

    def __len__(self):
        return len(self.tickets)

    def __iter__(self):
        return iter(self.tickets)

    def overdue(self, now=NOW):
        """Return the tickets past their SLA that are not closed."""
        late = []
        for t in self.tickets:
            if t.status != "closed" and now > t.deadline():
                log.warning("%s is past its SLA", t)
                late.append(t)
        return late


def ticket_refs(text):
    """Return the ticket numbers mentioned in a text."""
    refs = []
    for match in TICKET_REF.finditer(text):
        refs.append(int(match.group(1)))
    return refs


def redact(text):
    """Return the text with email addresses hidden."""
    return EMAIL.sub("[email]", text)
