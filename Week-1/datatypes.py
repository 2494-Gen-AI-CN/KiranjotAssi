#strings 
name = "    Login Page returns 500"
print(name)

print(name.strip()) #.strip is an instance method that removes whitespace from the beginning and end of a string, belongs to string class
print(name.strip().upper()) #.upper is an instance method that converts all characters in a string to uppercase, belongs to string class    
print (name.lower()) #.lower is an instance method that converts all characters in a string to lowercase, belongs to string class

print(name) #the string is unchanged because strings are immutable, meaning they cannot be changed after they are created.
name = name.strip()

print(name)
#slicing strings
print(name[4]) #prints the character at index 4
print(name[:5]) #prints the first 5 characters of the string
print(name[2:6]) #prints the characters from index 2 to 5
print(name[-3:]) #prints the last 3 characters of the string


print(name.replace("500", "error")) #.replace is an instance method that replaces a specified phrase with another specified phrase, belongs to string class

#list of strings
words = ["Login", "Page", "returns", "500"]

sentence = words[0] + words[1]
print(sentence)

new_sentence = " ".join(words)
print(new_sentence)

reporter = "Ada Lovelace"
formatted_report = f"{name} reported by {reporter}"
print(formatted_report) #f-strings are a way to format strings in Python, they allow you to embed expressions inside string literals, using curly braces {}.


#Casting
#turns a value of one type into another
ticket_id_from_user = input("Enter the ticket ID: ")
#input always returns a string, so we need to cast it to an int
ticket_id = int(ticket_id_from_user)

print(ticket_id , type(ticket_id), type(ticket_id_from_user)) #prints the ticket ID and its type

#converting a string to a floating point number
hours_open = float("5.5")

print(str(101) + " tickets")


hours_open = int(hours_open) #casting a float to an int will truncate the decimal part


#Booleans
#bool has two values: True and False. They are used to represent truth values in Python.
#everything in python is either Truthy or falsy

is_open = True

#0 is falsy
print(bool(0), bool(1), bool(-7))

#empty strings are falsy
print(bool(""), bool("Hello"))

#empty array is falsy
print(bool([]), bool([1,2,3]))

hours_left = 8 - hours_open 

#we can assign a boolean by checking conditions
is_breached = is_open and hours_left < 0

print(is_breached)


assignee = "" or "unassigned" #if the first value is falsy, the second value will be assigned
print(assignee)


#Lists
ticket_queue = ["Login Page returns 500", "Signup Page returns 404", "Profile Page returns 403"]
print(type(ticket_queue), len(ticket_queue)) #prints the type of the variable, which is a list, and its length

ticket_queue.append("Dashboard Page returns 502") #adds an item to the end of the list
ticket_queue.insert(1, "Settings Page returns 401") #adds an item to the list at a specific index
print(ticket_queue)

#Just like strings, we can slice and negative index lists
print(ticket_queue[1:3]) #prints the items from index 1 to 2
print(ticket_queue[3]) #prints the item at index 3

removed = ticket_queue.pop() #removes the last item from the list and returns it so it can be stored or otherwise used in your code
print(removed)
print(ticket_queue)

#Sorting Lists

#.sorted takes your list and returns a new list that is sorted, it does not change the original list
print(sorted(ticket_queue))
print(ticket_queue)

#call sort to sort the list in place, it changes the original list
print(ticket_queue.sort()) 
print(ticket_queue)


ticket_queue_alias = ticket_queue #this is a reference to the same list, not a copy (created a pointer)
ticket_queue_alias.append("New Ticket") #this will change the original list because they are the same list
print(ticket_queue) #accessing the list via the new reference alters the underlying list

#if I want an actual copy distinct in memory, use .copy()
ticket_queue_copy = ticket_queue.copy() #this is a distinct copy of the list, not a reference
ticket_queue_copy.append("Another Ticket in the copy") #this will not change the original list

print(ticket_queue) #accessing the list via the new reference does not alter the underlying list
print(ticket_queue_copy) #accessing the list via the new reference does not alter the underlying list

#Binary Types
#when we try to export anything to save it to a disk, we are serializing it as a Binary stream of literal bytes
note = "café"

raw = note.encode("utf-8") #.encode is an instance method that encodes a string into bytes, belongs to string class
print(len(note), len(raw))


#bytearray lets us treat it as spearate bytes. We can then use it as a list of bytes
buffer = bytearray(raw) #bytearray is a mutable sequence of bytes, it can be modified in place
buffer.append(33) #adds a byte to the end of the bytearray
print(buffer.decode("utf-8")) #.decode is an instance method that decodes bytes into a string, belongs to bytes class


#Nontype - None means "no value here" 
#in Python, it is its own type, with exactly one value: None

assignee = None
print(assignee, type(assignee)) #prints the value of assignee and its type, which is NoneType

#if we want to compare things that are/may be None, we use ==
print(assignee is None)
print(assignee is not None)

#Datetime - points in time, timestamps, length of time
#comes up a lot when working with datasets 
#don't need to install new packages
from datetime import datetime, timedelta

#datetime is an object, not a primitive built in type. We are calling a constructor here, and satisfying the arguments of 
#one of the datetime classes many constructors. 
opened = datetime(2026, 10, 12, 11, 17)
print(opened, type(opened)) #prints the value of opened and its type, which is datetime.datetime

#SLA - service level agreement - how long it should take to resolve a ticket
sla = timedelta(hours=4)
due = opened + sla #adding a timedelta to a datetime gives us a new datetime
print(due)

#Give me the time right now, based on system time
now = datetime.now() #gets the current date and time
print(now)


age = now - opened #subtracting two datetimes gives us a timedelta
print(age.total_seconds())

print(opened.isoformat())
print(opened.strftime("%Y-%m-%d %H")) #.strftime is an instance method that formats a datetime into a string, belongs to datetime class

parsed_date = datetime.strptime("2026-10-12 11:17", "%Y-%m-%d %H:%M") #.strptime is an instance method that parses a string into a datetime, belongs to datetime class
print(parsed_date)


#sets - unordered collections of unique items
#dictonaries - unordered collections of key-value pairs