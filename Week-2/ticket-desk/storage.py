"""Plain-text files for the desk: read, write, append and delete.
    Tickets saved as JSON"""
from pathlib import Path
import json # The default json library - works with files, as well as streams, etc
from datetime import datetime
from desk import Desk, Ticket
import logging

log = logging.getLogger(__name__) # adding a logger 

# Creating a read function
def read_lines(path):
    """Return the lines of a text file as a list, without line endings.
        Opens the file (if it exists) and returns the contents, as a list
        of strings. Each line of the file is it's own string in the list."""
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()

# Function to export the tickets that belong to a specific desk object
def export_board(desk, path):
    """Write one tab-separated line per ticket. NOTE: this replaces the contents
        of the file when it runs."""
    with open(path, "w", encoding='utf-8') as f:
        for t in desk:
            # Represent the ticket as a list of strings
            fields = [str(t.ticket_id), t.title, t.priority, t.status]
            # Write those strings to the file, with a newline char at the end
            f.write("\t".join(fields) + "\n")
            # "2        Sample title    low     closed"
            # "3    etc    etc   etc"       
    
def append_line(path, text):
    """Add one line of text to the end of a file, don't truncate the file"""
    with open(path, "a", encoding='utf-8') as f:
        f.write(text + "\n")
        
def delete_file(path):
    """Deletes the file at a given path and returns True,
        returns False if the file is missing"""
    try:
        Path(path).unlink() # if the file exists, delete it
    except FileNotFoundError:
        return False
    
    return True

# JSON Area

def to_record(ticket):
    """Return the ticket as a dict of plain values JSON can hold."""
    closed = None
    # Check the none property to see if it contains a datetime. 
    # if it does, we have to handle that
    if ticket.closed_at is not None:
        closed = ticket.closed_at.isoformat() # return a string of the datetime for us
    
    return {
        "ticket_id": ticket.ticket_id,
        "title": ticket.title,
        "priority": ticket.priority,
        "status": ticket.status,
        "assignee": ticket.assignee,
        "opened_at": ticket.opened_at.isoformat(),
        "closed_at": closed
    }

def from_record(record):
    """Rebuild a ticket from a dict made by to_record"""
    # Because we used iso-format, we can easily create a datetime object
    # in our running app using fromisoformat()
    opened = datetime.fromisoformat(record["opened_at"])
    
    # we can start constructing our ticket
    file_ticket = Ticket(record["ticket_id"], record["title"], record["priority"], opened)
    
    # Manually setting these properties in our new Ticket object based on the dictionary 
    # that we de-serialized from the JSON file
    file_ticket.status = record["status"]
    file_ticket.assignee = record["assignee"]
    
    # We have to handle closed_at separately, same as when we serialized
    if record["closed_at"] is not None:
        file_ticket.closed_at = datetime.fromisoformat(record["closed_at"])
    
    return file_ticket

# The methods above help to serialize/deserialize our Ticket objects
# They are helpers for the methods below, which actually do the file IO

def save_desk(desk, path):
    """Write every Ticket in the desk to a JSON file."""
    records = [] # will contain a list of dictionaries
    
    # Using our to_record to create the ticket dictionary representations
    for ticket in desk:
        records.append(to_record(ticket))
        
    with open(path, "w", encoding="utf-8") as f:
        # instead of writing our own custom logic like we did above
        # we just call json.dumps. If we pass it something that can be 
        # serialized to JSON (dictionaries can) - it will write it 
        # to the file
        json.dump(records, f, indent=2)
        
def load_desk(path):
    """Return the desk saved in the file, or an empty desk object
        if there is none"""
    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        return Desk() # if the file doesn't exist, return an empty Desk object
    except json.JSONDecodeError as err:
        log.error("cannot read %s: %s", path, err)
        raise ValueError(f"{path} is not valid JSON") from err
    
    desk = Desk() # create an empty desk object
    
    for record in records:
        desk.add(from_record(record)) 
    
    return desk
    
    
