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
    
    Investigate the house, question the suspects, and solve the mystery before the deadline is up. 
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

def interrogate(found_clues, questioned):
    print("\n Who would you like to interrogate? ")
    for key, suspect in SUSPECTS.items():
        print(f"{key}.{suspect['name']}")

    choice = input ("Suspect number: ").strip()

    if choice not in SUSPECTS:
        print("Invalid suspect.")
        return 

    suspect = SUSPECTS[choice]
    questioned.add(choice)

    heading(suspect["name"])
    print(f"Alibi: {suspect['alibi']}")
    print(f"Motive: {suspect['motive']}")
    print(f"\nStatement: {suspect['statement']}")

    if choice == "2" and "note" in found_clues:
        print(
            "\n You mention the note addressed to T.R. "
            "Thomas becomes visibly uncomfortable. "
        )
        print('"Victor was always suspicious of everyone," he says.')

def review_notebook(found_clues, questioned, solved):
    heading("CASE NOTEBOOK")

    print("\nEvidence collected: ")
    if not found_clues:
        print("No evidence collected yet.")
    else:
        for clue_id in found_clues:
            print(f"- {CLUE_NAMES[clue_id]}")

    print("\nSuspects questioned: ")

    if not questioned:
        print("No suspects questioned yet.")
    else:
        for key in sorted(questioned):
            print(f"- {SUSPECTS[key]['name']}")
    print("\nTimeline Puzzle: ")
    print("Solved" if solved else "Not solved")


def solve_timeline(found_clues, solved):
    heading("THE TIMELINE PUZZLE")

    print("""
    Victor's death is estimated to have occurred around 10:25pm.
    Daniel claims he saw Thomas carrying a silver tray shortly after 10:20pm.
    Thomas claims he never took a tray into the study.
    The note found in the study specifically requested a meeting with T.R. at 10:20pm.
     
    Question: Which suspect's story deserves the closest scrutiny?""") 

    if len(found_clues) < 2:
        print("\nYou need to collect at least two clues first")
        return solved

    print("1. Elanor Redwood")
    print("2. Thomas Reed")
    print("3. Daniel Redwood")
    print("4. Dr. Maya Chen")

    answer = input("Your Deduction: ").strip()

    if answer == CULPRIT:
        print("\nCorrect Deduction! Thomas' denial conflicts with "
              "Daniel's account, and the note gives a possible motive. ")
        return True
    print("That deduction doesn't seem to fit the evidence yet. ")
    return solved


def accuse(found_clues, questioned, solved):
    heading("FINAL ACCUSATION")
    print("Who do you believe killed Victor?")

    for key, suspect in SUSPECTS.items():
        print(f"{key}. {suspect['name']}")

    choice = input("Your accusation: ").strip()

    if choice not in SUSPECTS:
        print("Invalid suspect.")
        return False
    
    score = (
        len(found_clues) * 10
        + len(questioned) * 5
        + (25 if solved else 0)
    )

    heading("CASE CLOSED")

    if choice == CULPRIT:
        print("Congratulations! You identified the culprit!")
        print("The note, suspicious bottle, and conflicting")
        print("statements helped expose Thomas Reed.")
    else:
        print(f"You accused {SUSPECTS[choice]['name']}, but that was incorrect.")
        print(f"The actual culprit was {SUSPECTS[CULPRIT]['name']}.")
        print("Review the evidence and try to solve the case again.")

    print(f"\nDetective score: {score}")

    if score >= 70:
        print("Rank: Master Detective")
    elif score >= 40:
        print("Rank: Skilled Investigator")
    else:
        print("Rank: Rookie Detective")

    return True

def main():
    found_clues = set()
    questioned = set()
    solved = False

    show_intro()

    while True: 
        show_menu()
        choice = input("Choose an action: ").strip()

        if choice == "1":
            investigate(found_clues)
        elif choice == "2":
            interrogate(found_clues, questioned)
        elif choice == "3":
            review_notebook(found_clues, questioned, solved)
        elif choice == "4":
            solved = solve_timeline(found_clues, solved)
        elif choice == "5":
            if accuse(found_clues, questioned, solved):
                break
        elif choice == "6":
            print("Investigation suspended. Goodbye, detective.")
            break
        else:
            print("Invalid choice. Enter a number from 1 to 6.")


if __name__ == "__main__":
    main()