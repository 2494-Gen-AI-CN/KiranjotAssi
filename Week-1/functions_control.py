#inheriting from the base error class to create a custom exception --> interview question

#branching - control flow logic

#if, elif, else - picks one branch. the first one that satisifes it's condition check, subsequent ones are skipped. 
from datetime import datetime, timedelta

SLA_HOURS = {"high": 4, "normal": 24, "low": 72}

PRIORITY_RANK = {"high": 1, "normal": "2", "low": 3}

NOW = datetime(2026, 10, 16, 14, 0)

queue = [
    {"id" : 101, "title": "Login page returns 500", "priority": "high", "opened_at": datetime(2026, 10, 16, 8, 0), "open": True},
    {"id" : 102, "title": "Printer Jams", "priority": "normal", "opened_at": datetime(2026, 10, 15, 15, 30), "open": True},
    {"id" : 103, "title": "Typo on footer", "priority": "low", "opened_at": datetime(2026, 10, 13, 9, 0), "open": False}
]

print(len(queue), "Tickets Loaded")



ticket = queue[1] #grabbing printer jam ticket
deadline = ticket["opened_at"] + timedelta(hours=SLA_HOURS[ticket["priority"]])

hours_left = (deadline - NOW).total_seconds() / 3600 #how many hours are left to resolve the ticket

print(ticket["title"], "hours_left: ", hours_left)


if hours_left < 0:
    status = "breached"
elif hours_left < 2:
    status = "at risk"
else:
    status = "on time"

print("Status: ", status)

title = ticket["title"]

if not title:
    print("ticket lacks a title")

if "Printer" in title: 
    print("Mentions the printer")

if 0<= hours_left <24:
    print("Due within a day")

if not ticket["open"]:
    print("closed")
else: 
    print("still open")


#we can nest these checks if we want to. I fyou're more than two deep, reevaluate

if ticket["open"]:
    if hours_left < 2:
        if ticket["priority"] != "low":
            print("We should escalate this")

state = "open" if ticket["open"] else "closed"
print(state)

#Loops
attempts = ["urgent", "MED", "high"]
tries = 0

#while loop repeats while a condition stays true. we check before every run through the code in the loop

while tries < len(attempts):
    answer = attempts[tries].strip().lower()
    tries += 1

    if answer in SLA_HOURS:
        print("accepted", answer, "after", tries, "tries")
        break #exiting the loop if this is satisfied

    print("not a priority", answer)
else: 
    print("User gave up") # if loop run terminates with no break, we can use an else to run default code 

# If I want an infinite loop, i can use while/true. this will continue until a break.
# If I use a variable that is set to false, I can then manually set it to true, using it as a completion flag

# for loops - in python, for loops can look different. loops in python are optimized for work with collections

#t represents an item in the queue list
for t in queue:
    print(t["id"], t["title"])

#index represents the ticket (t's) place in the list. I use start in enumerate to tell it to count from 1, rather than 0
for index, t in enumerate(queue, start=1):
    print(f"{index}, {'title'}")

for priority, hours in SLA_HOURS.items():
    print(f"{priority:<8}-{hours:>4}h")


#IT call center agents 
agents = ["dana", "lee", "sam"]
#creating a tuple (you can't change it once its created) -> enforces dev behaviour
for t, agent in zip(queue, agents):
    print(t["id"], "->", agent)

for n in range(1,4): #I can use the range function if i need a loop that fires x number of times exactly
    print("ping", n)

print("after the loop n is still", n)


#Switch statements in Python
#we use match case, exactly like a switch in other languages
#python does not support c style case fallthrough, so ending each case with break is not required
match ticket["priority"]:
    case "low": 
        print("this ticket is low priority")
    case "high":
        print("this ticket is high priority")
    case _ :#this underscore wildcard acts as our default case
        print("normal ticket")

# functions are reusable bits of logic. you can write them once and call them anywhere else
# we can import functions to other files and reuse them across programs

def deadline_for(ticket):
    """Return the datetime by which this ticket must be closed"""
    return ticket["opened_at"] + timedelta(hours=SLA_HOURS[ticket["priority"]])


print(deadline_for(queue[0]))

print(deadline_for.__doc__)


def describe (ticket):
    """returns a pre-formatted ticket description"""
    print(f"#{ticket['id']} {ticket['title']} - {ticket['priority']}")


result = describe(queue[0])
print(result) #return statement is missing. This will return none

#I can give my functions default argument values
def hours_left_for(ticket, now = datetime.now()):
    return (deadline_for(ticket) - now).total_seconds() /3600
#if i provide a default argument for my function, I can omit it from from function call if i am okay with the default value
print(hours_left_for(queue[1]))
#here i provide my own value for now, the default is not used. 
print(hours_left_for(queue[1]), now=NOW)

#finally, if i use arg_name = value, I can put my args in any order
print(hours_left_for(now=NOW, ticket= queue[0]))


def status_for(ticket, now =NOW):
    """closed, breached, at risk, or on time"""
    if not ticket["open"]:
        return "closed"
    hours = hours_left_for(ticket, now)


    if hours <0:
        return "breached"
    if hours < 2: 
        return "At risk"
    
    return "on time"


#a trap about lists (dictionaries and other collections and functions)

def log(entry, history = []):
    history.append(entry)
    return history


print(log("opened"))
print(log("assigned"))


def log_safely(entry, history=None):
    if history is None:
        history = []
    history.append(entry)
    return history

#Lambdas and sort keys
# lambdas - builds a one expression function, no name, right where its used. 
# commonly used to satisfy sorting methods, writing comparsion logic, and when making API calls

# in general we want to use def to define named functions
double = lambda n: n *2 #notice: no return keyword. whatever the expression evaluates to is assumed to be the return 

by_text = sorted(queue, key=lambda t: t["priority"])
for t in by_text:
    print(t["priority"], t["title"]) # alphabetical - because what we asked for, was to sort off the value of the strings that correspond to the priority key, 
    # not what we actually wanted
    # we will revisit comparisons later

#we've worked with lists, lets look at actual python arrays
from array import array

hours_open = array("d", [6.0, 22.5, 1.5]) # "d" - every item is a float
hours_open.append(0.0)


#Classes and objects
#a class bundles data amd methods that act on that data - Encapsulation an object
# is an instance of a class. Created using the class as a blueprint

#If we want access modifiers, we can use them, but there's only two and they're convention
class Ticket:
    """One suppoised ticket the rules that belong to it"""
    #this init is the constructor - this is in reference to the object that is created
    def __init__(self, ticket_id, title, priority, opened_at = datetime.now ):
        self.ticket_id = ticket_id
        self.title = title
        self.priority = priority
        self.__opened_at = opened_at #If we use a double underscore, we get a private field/property. This is sort-of enforced
        self._assignee = None #underscore on a property denotes "protected", intended for internal or sublass use only
        self.is_open = True

    def deadline(self):
        return self.__opened_at + timedelta(hours=SLA_HOURS[self.priority])

    def assign(self, agent):
        self.assignee = agent

    def close(self):
        self.is_open = False

    #if we want to print our object out, we override the __str__ method
    def __str__(self):
        return f"{self.ticket_id} {self.title} {self.priority}"


t1 = Ticket(101, "Login page returns 500", "high")
print(type(t1))
print(t1.ticket_id)
print(t1._assignee) #This is a human signal, not enforced
print(t1.__opened_at) #when we give a property a double underscore, python uses "name mangling" to enforce it. 

#in python I can ad/remove things from a runtime object
t1.new_property = "New"
print(t1.new_property)

del t1.new_property


print(t1)

#Inheritance
class UrgentTicket(Ticket):
    """ A ticket that gets half the normal time"""
    def __init__(self, ticket_id, title, priority, opened_at, manager):
        self.manager = manager
        super().__init__( ticket_id, title, priority, opened_at) #passing args to parent class constructor 
        
    #overriding the deadline function
    def deadline(self):
        normal = super().deadline()
        self.__opened_at + (normal - self.__opened_at)/2
        #cut our time in half

