"""Report on the desk's tickets with the Collections module"""
from collections import Counter, namedtuple, OrderedDict, defaultdict

# Defining our namedtuple
TicketRow = namedtuple("TicketRow", ["ticket_id", "priority", "status", "hours"])

def status_counts(desk):
    """Return how many tickets are in each status"""
    statuses = []
    
    for t in desk:
        statuses.append(t.status)
    
    return Counter(statuses) 

def rows(desk):
    """Return one TicketRow per ticket; hours is None while it is open"""
    table = [] # This will hold a "table" - a list of named tuples
    # think of what is in here like an excel table. 
    # [
    #     (1, "low"....),
    #     (2, "low"....),
    #     (3, "high"....),
    # ]
    
    for t in desk:
        hours = None # open tickets have no resolution time yet
        # Calculate resolution time if the ticket is closed
        if t.closed_at is not None:
            hours = (t.closed_at - t.opened_at).total_seconds() / 3600
        
        table.append(TicketRow(t.ticket_id, t.priority, t.status, hours))
    
    return table
    
def work_queue(desk):
    """Return unfinished tickets by id, soonest deadline first"""
    waiting = [] # list to hold tickets waiting to be resolved
    
    # Loop through tickets in the desk - grab all open tickets
    for t in desk:
        if t.status != "closed":
            waiting.append(t)
    
    queue = OrderedDict()
    
    # for every ticket in our now sorted list
    for t in sorted(waiting, key=lambda t: t.deadline()):
        queue[t.ticket_id] = t # use the ticket_id as key, whole ticket as value
    
    return queue

def by_agent(desk):
    """Return the ticket_ids held by each tech support agent"""
    # Create a defaultdict - key is agent name, value is a list of ticket_id's
    # that are assigned to them
    groups = defaultdict(list)
    
    for t in desk:
        if t.assignee is not None:
            groups[t.assignee].append(t.ticket_id)
    
    return groups
    
            