import textwrap

CASE_TITLE = "MURDER AT REDWOOD MANOR"


SUSPECTS = {
    "1": {
        "name": "Elanor Redwood",
        "role": "The Wife",
        "alibi": "I was reading in the library from 10:15 to 10:45",
        "motive": "Victor had recently changed his will",
        "statement": "I heard footsteps in the hallway around 10:20"
    },
    "2": {
        "name": "Thomas Reed",
        "role": "The butler",
        "alibi": "I was preparing drinks in the kitchen all evening",
        "motive": "Victor suspected someone was stealing from his cellar",
        "statement": "I never took a drink into the study tonight"
    },
    "3": {
        "name": "Daniel Redwood",
        "role": "The son",
        "alibi": "I was on the terrace from 10:10 to 10:35",
        "motive": "Victor refused to pay his gambling debts",
        "statement": "I saw Thomas carrying a silver tray shortly after 10:20"
    },
    "4": {
        "name": "Dr. Maya Chen",
        "role": "The doctor",
        "alibi": "I was examining a patient in the guest room",
        "motive": "Victor knew about a serious mistake I made once",
        "statement": "Victor's drink was tampered with before he died"
    }
}

LOCATIONS = {
        "study": {
            "description": "Victor's study smells faintly of whiskey",
            "clue": ("A handwritten note reads: 'I know who has been stealing from the cellar. Speak to T.R. at 10:20'."
            ),
            "id": "note" 
        },
        "kitchen": {
            "description": "Glasses and bottles cover the ktichen counter",
            "clue": ("You find a bottle containing a suspicious chemical "
                        "residue beside the drinks cabinet"
            ),
            "id": "bottle" 
        },
        "library": {
            "description": "The library is quiet, with a chair near the window",
            "clue": ("A clock shows 10:25 PM. Elanor says she was here, "
                        "but the chair is cold and an untouched book lies open."
            ),
            "id": "library" 
        },
        "terrace":{
            "description": "Rain has left the terrace stones wet ",
            "clue": ("you discover wet footprints leading from the terrace"
                        "towards the kitchen entrance "
            ),
            "id": "footprints" 
        }
}

CLUE_NAMES ={
    "note" : "The warning note",
    "bottle" : "The suspicious bottle",
    "library" : "The untouched book",
    "footprints" : "The wet footprints"
}

#intended solution: Thomas is the culprit
CULPRIT = "2"

def line():
    print ("-" * 55)

def heading(title):
    line()
    print(title.upper())
    line()


def show_intro():
    heading(CASE_TITLE)
    print(textwrap.dedent("""
    Victor Redwood is dead. 
    
    Four people were inside the manor that evening. Everyone has an alibi. Everyone has a secret.
    
    Investigate the house, quetsion the suspects, and solve the mystery before the deadline is up. 
    Don't get caught, because the murderer is somewhere in the house.""" ).strip())

def show_menu():
    print("""
    1. Investigate a location
    2. Interrogate a suspect
    3. Review case notebook
    4. Solve the timeline puzzle
    5. Accuse someone
    6. Quit game
    """)

def investigate(found_clues):
    locations = list(LOCATIONS.keys())

    print("\nLocations: ")
    for i, location in enumerate(locations, start=1):
        print(f"{i}.{location.title()}")
    
    choice = input("Where would you like to investigate? ").strip()

    if not choice.isdigit():
        print("Please enter a location number. ")
        return

    index = int(choice) - 1
    if index <0 or index>=len(locations):
        print("That location doesn't exist")
        return
    
    location = locations[index]
    details = LOCATIONS[location]

    print(f"\n{details['description']}")
    clue_id = details["id"]


    if clue_id in found_clues:
        print("You've already documented the evidence here.")
    else:
        print(f"\nEVIDENCE FOUND: {details['clue']}")
        found_clues.add(clue_id)