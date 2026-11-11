
import tkinter as tk
from tkinter import messagebox
import random

# --------------------------------------------------
# CASE DATA
# --------------------------------------------------

SUSPECTS = {
    "1": {
        "name": "Eleanor Redwood",
        "role": "Victor's wife",
        "motive": "A bitter dispute over Victor's inheritance.",
        "alibi": "Claims she was in her bedroom."
    },
    "2": {
        "name": "Thomas Reed",
        "role": "The butler",
        "motive": "Victor threatened to expose his secret.",
        "alibi": "Claims he was preparing tea."
    },
    "3": {
        "name": "Daniel Redwood",
        "role": "Victor's son",
        "motive": "He stood to inherit the family estate.",
        "alibi": "Claims he was in the library."
    },
    "4": {
        "name": "Dr. Maya Chen",
        "role": "Family physician",
        "motive": "Victor knew something about her past.",
        "alibi": "Claims she left before the murder."
    }
}

CULPRIT = "2"

LOCATIONS = {
    "The Study": {
        "clue": "note",
        "title": "The Torn Note",
        "description": (
            "A torn note lies beneath Victor's desk. "
            "It reads: 'Meet me before midnight. "
            "No one must know.' The initials T.R. "
            "are written at the bottom."
        )
    },
    "The Kitchen": {
        "clue": "bottle",
        "title": "The Suspicious Bottle",
        "description": (
            "Behind a row of tea tins, you discover "
            "a small bottle with a bitter chemical smell. "
            "Someone tried to hide it."
        )
    },
    "The Library": {
        "clue": "footprints",
        "title": "Muddy Footprints",
        "description": (
            "Muddy footprints lead from the library "
            "toward a service corridor. Their timing "
            "does not match one suspect's alibi."
        )
    },
    "The Terrace": {
        "clue": "watch",
        "title": "The Broken Watch",
        "description": (
            "A broken pocket watch lies beside the "
            "terrace door. Its hands stopped shortly "
            "before midnight."
        )
    }
}

# --------------------------------------------------
# GAME STATE
# --------------------------------------------------

found_clues = set()
questioned = set()
solved_timeline = False
game_finished = False

# --------------------------------------------------
# COLORS
# --------------------------------------------------

BG = "#151816"
PANEL = "#222722"
PANEL_LIGHT = "#2D342D"
GOLD = "#C8A96B"
CREAM = "#F1E8D5"
MUTED = "#AAAFA6"
GREEN = "#75866A"
RED = "#A65B50"

# --------------------------------------------------
# MAIN WINDOW
# --------------------------------------------------

root = tk.Tk()
root.title("Case Files: Redwood Manor")
root.geometry("1100x720")
root.minsize(900, 620)
root.configure(bg=BG)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

header = tk.Frame(root, bg=BG, padx=28, pady=20)
header.pack(fill="x")

tk.Label(
    header,
    text="CASE FILES",
    bg=BG,
    fg=GOLD,
    font=("Georgia", 12, "bold")
).pack(anchor="w")

tk.Label(
    header,
    text="MURDER AT REDWOOD MANOR",
    bg=BG,
    fg=CREAM,
    font=("Georgia", 25, "bold")
).pack(anchor="w", pady=(4, 0))

tk.Label(
    header,
    text="CASE 001  •  THE DEATH OF VICTOR REDWOOD",
    bg=BG,
    fg=MUTED,
    font=("Consolas", 10)
).pack(anchor="w", pady=(5, 0))

# --------------------------------------------------
# MAIN LAYOUT
# --------------------------------------------------

body = tk.Frame(root, bg=BG, padx=28, pady=8)
body.pack(fill="both", expand=True)

sidebar = tk.Frame(body, bg=PANEL, width=210, padx=16, pady=18)
sidebar.pack(side="left", fill="y", padx=(0, 18))
sidebar.pack_propagate(False)

content = tk.Frame(body, bg=BG)
content.pack(side="left", fill="both", expand=True)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

tk.Label(
    sidebar,
    text="INVESTIGATION",
    bg=PANEL,
    fg=GOLD,
    font=("Consolas", 10, "bold")
).pack(anchor="w", pady=(0, 18))


# --------------------------------------------------
# SHARED HELPERS
# --------------------------------------------------

def clear_content():
    for widget in content.winfo_children():
        widget.destroy()


def section_title(title, subtitle=""):
    tk.Label(
        content,
        text=title,
        bg=BG,
        fg=CREAM,
        font=("Georgia", 20, "bold")
    ).pack(anchor="w", pady=(0, 6))

    if subtitle:
        tk.Label(
            content,
            text=subtitle,
            bg=BG,
            fg=MUTED,
            font=("Arial", 10)
        ).pack(anchor="w", pady=(0, 18))


def make_button(parent, text, command, color=PANEL_LIGHT):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=CREAM,
        activebackground=GOLD,
        activeforeground=BG,
        relief="flat",
        cursor="hand2",
        font=("Arial", 11, "bold"),
        padx=14,
        pady=10
    )


def update_status():
    status_label.config(
        text=f"EVIDENCE COLLECTED: {len(found_clues)} / "
             f"{len(LOCATIONS)}"
    )


# --------------------------------------------------
# OVERVIEW SCREEN
# --------------------------------------------------

def show_overview():
    clear_content()

    section_title(
        "The Investigation",
        "A death. Four suspects. One truth."
    )

    story = (
        "Victor Redwood was discovered dead in his "
        "study shortly before midnight.\n\n"
        "The manor was locked against a violent storm. "
        "Four people were inside, and each has a reason "
        "to hide something.\n\n"
        "Explore the manor, gather evidence, question "
        "the suspects, and determine who killed Victor."
    )

    story_box = tk.Label(
        content,
        text=story,
        justify="left",
        anchor="nw",
        wraplength=620,
        bg=PANEL,
        fg=CREAM,
        font=("Georgia", 13),
        padx=22,
        pady=24
    )
    story_box.pack(fill="x", pady=(0, 20))

    make_button(
        content,
        "BEGIN INVESTIGATION",
        show_locations,
        GOLD
    ).pack(anchor="w")


# --------------------------------------------------
# LOCATION SCREEN
# --------------------------------------------------

def show_locations():
    clear_content()

    section_title(
        "Explore the Manor",
        "Select a location to search for evidence."
    )

    for location, details in LOCATIONS.items():
        required = {
            "The Study": set(),
            "The Kitchen": {"note"},
            "The Library": {"bottle"},
            "The Terrace": {"bottle"}
        }.get(location, set())

        unlocked = required.issubset(found_clues)

        if unlocked:
            label = location
            command = lambda loc=location: investigate(loc)
            color = PANEL
        else:
            label = f"{location}  —  LOCKED"
            command = lambda: messagebox.showinfo(
                "Location Locked",
                "Find the required evidence to unlock "
                "this location."
            )
            color = "#1B1F1C"

        card = tk.Frame(
            content,
            bg=color,
            padx=16,
            pady=14
        )
        card.pack(fill="x", pady=5)

        tk.Label(
            card,
            text=label,
            bg=color,
            fg=GOLD if unlocked else MUTED,
            font=("Georgia", 14, "bold")
        ).pack(side="left")

        make_button(
            card,
            "INVESTIGATE" if unlocked else "LOCKED",
            command
        ).pack(side="right")

    update_status()


def investigate(location):
    details = LOCATIONS[location]
    clue = details["clue"]

    if clue in found_clues:
        messagebox.showinfo(
            location,
            "You've already collected the evidence here."
        )
        return

    answer = messagebox.askyesno(
        details["title"],
        details["description"] + "\n\nAdd this evidence "
        "to your case notebook?"
    )

    if answer:
        found_clues.add(clue)
        update_status()

        messagebox.showinfo(
            "Evidence Collected",
            f"Added to your notebook:\n\n"
            f"{details['title']}"
        )

        show_locations()


# --------------------------------------------------
# SUSPECTS SCREEN
# --------------------------------------------------

def show_suspects():
    clear_content()

    section_title(
        "Suspect Interviews",
        "Compare statements with the evidence."
    )

    for key, suspect in SUSPECTS.items():
        card = tk.Frame(content, bg=PANEL, padx=16, pady=12)
        card.pack(fill="x", pady=5)

        tk.Label(
            card,
            text=suspect["name"],
            bg=PANEL,
            fg=GOLD,
            font=("Georgia", 14, "bold")
        ).pack(anchor="w")

        tk.Label(
            card,
            text=suspect["role"],
            bg=PANEL,
            fg=MUTED,
            font=("Arial", 10)
        ).pack(anchor="w", pady=(2, 8))

        make_button(
            card,
            "INTERROGATE",
            lambda k=key: interrogate(k)
        ).pack(anchor="w")


def interrogate(key):
    suspect = SUSPECTS[key]
    questioned.add(key)

    dialogue = (
        f"{suspect['name']}\n"
        f"{'─' * 30}\n\n"
        f"Motive:\n{suspect['motive']}\n\n"
        f"Alibi:\n{suspect['alibi']}\n\n"
    )

    if key == CULPRIT and "note" in found_clues:
        dialogue += (
            "You mention the note marked T.R.\n\n"
            "Thomas hesitates. 'Those initials could "
            "belong to anyone,' he says."
        )
    elif key == CULPRIT and "bottle" in found_clues:
        dialogue += (
            "You mention the suspicious bottle.\n\n"
            "Thomas looks uncomfortable and insists "
            "he never entered the kitchen."
        )
    else:
        dialogue += (
            "You record the statement in your notebook. "
            "More evidence may help you test this alibi."
        )

    messagebox.showinfo("Interview", dialogue)


# --------------------------------------------------
# EVIDENCE NOTEBOOK
# --------------------------------------------------

def show_evidence():
    clear_content()

    section_title(
        "Evidence Notebook",
        "Every clue you've collected so far."
    )

    if not found_clues:
        tk.Label(
            content,
            text="Your notebook is empty. Start by "
                 "investigating the study.",
            bg=BG,
            fg=MUTED,
            font=("Georgia", 12)
        ).pack(anchor="w")
        return

    for details in LOCATIONS.values():
        if details["clue"] in found_clues:
            card = tk.Frame(content, bg=PANEL, padx=16, pady=14)
            card.pack(fill="x", pady=5)

            tk.Label(
                card,
                text=details["title"],
                bg=PANEL,
                fg=GOLD,
                font=("Georgia", 14, "bold")
            ).pack(anchor="w")

            tk.Label(
                card,
                text=details["description"],
                bg=PANEL,
                fg=CREAM,
                justify="left",
                wraplength=600,
                font=("Arial", 10)
            ).pack(anchor="w", pady=(6, 0))


# --------------------------------------------------
# TIMELINE PUZZLE
# --------------------------------------------------

def show_timeline():
    global solved_timeline

    clear_content()

    section_title(
        "Reconstruct the Timeline",
        "Use the evidence to determine the critical time."
    )

    tk.Label(
        content,
        text=(
            "Victor was killed shortly before midnight.\n\n"
            "The broken watch stopped before midnight. "
            "The note asks someone to meet Victor before "
            "midnight.\n\n"
            "What time do you believe the meeting was "
            "supposed to take place?"
        ),
        bg=PANEL,
        fg=CREAM,
        justify="left",
        wraplength=600,
        padx=20,
        pady=20,
        font=("Georgia", 12)
    ).pack(fill="x", pady=(0, 18))

    answer = tk.StringVar(value="")

    for option in ["9:00 PM", "10:30 PM", "11:45 PM", "12:30 AM"]:
        tk.Radiobutton(
            content,
            text=option,
            variable=answer,
            value=option,
            bg=BG,
            fg=CREAM,
            selectcolor=PANEL,
            activebackground=BG,
            activeforeground=GOLD,
            font=("Arial", 11)
        ).pack(anchor="w", pady=4)

    def check_answer():
        global solved_timeline

        if answer.get() == "11:45 PM":
            solved_timeline = True
            messagebox.showinfo(
                "Timeline Solved",
                "Correct. The evidence suggests the "
                "meeting was planned for 11:45 PM."
            )
        else:
            messagebox.showwarning(
                "Not Quite",
                "That timeline doesn't fit the evidence. "
                "Review your notebook and try again."
            )

    make_button(
        content,
        "CHECK TIMELINE",
        check_answer,
        GOLD
    ).pack(anchor="w", pady=16)


# --------------------------------------------------
# FINAL ACCUSATION AND ENDINGS
# --------------------------------------------------

def show_accusation():
    global game_finished

    clear_content()

    section_title(
        "Make Your Accusation",
        "Once you accuse someone, the case will close."
    )

    if not found_clues:
        tk.Label(
            content,
            text="You have no evidence yet. Investigate "
                 "the manor before making an accusation.",
            bg=BG,
            fg=RED,
            font=("Arial", 11)
        ).pack(anchor="w", pady=10)
        return

    choice = tk.StringVar(value="")

    for key, suspect in SUSPECTS.items():
        tk.Radiobutton(
            content,
            text=suspect["name"],
            variable=choice,
            value=key,
            bg=BG,
            fg=CREAM,
            selectcolor=PANEL,
            activebackground=BG,
            activeforeground=GOLD,
            font=("Arial", 12)
        ).pack(anchor="w", pady=6)

    def close_case():
        global game_finished

        if not choice.get():
            messagebox.showwarning(
                "Choose a Suspect",
                "Select a suspect before submitting."
            )
            return

        if not messagebox.askyesno(
            "Confirm Accusation",
            "Are you sure? This will end your investigation."
        ):
            return

        game_finished = True

        critical = {"note", "bottle", "footprints"}
        thorough = (
            critical.issubset(found_clues)
            and solved_timeline
        )

        if choice.get() == CULPRIT and thorough:
            title = "ENDING: MASTER DETECTIVE"
            ending = (
                "You correctly identify Thomas Reed.\n\n"
                "The note, bottle, and footprints expose "
                "his lies. Your timeline leaves no room "
                "for doubt.\n\n"
                "Victor's killer has been brought to justice."
            )
        elif choice.get() == CULPRIT:
            title = "ENDING: JUSTICE WITH DOUBTS"
            ending = (
                "You identify Thomas Reed, but your case "
                "is incomplete.\n\n"
                "Some critical evidence is still missing, "
                "and questions remain about the timeline."
            )
        elif thorough:
            title = "ENDING: THE WRONG CONCLUSION"
            ending = (
                f"You accuse {SUSPECTS[choice.get()]['name']}.\n\n"
                "Despite collecting the evidence, you "
                "draw the wrong conclusion. Thomas Reed "
                "escapes justice."
            )
        else:
            title = "ENDING: CASE LEFT OPEN"
            ending = (
                f"You accuse {SUSPECTS[choice.get()]['name']}.\n\n"
                "Your investigation was incomplete. "
                "The evidence doesn't support your theory, "
                "and Victor's murder remains unresolved."
            )

        messagebox.showinfo(title, ending)

        clear_content()
        section_title("Case Closed", title)
        tk.Label(
            content,
            text=ending,
            bg=PANEL,
            fg=CREAM,
            justify="left",
            wraplength=600,
            padx=20,
            pady=24,
            font=("Georgia", 13)
        ).pack(fill="x")

        make_button(
            content,
            "PLAY AGAIN",
            restart_game,
            GOLD
        ).pack(anchor="w", pady=18)

    make_button(
        content,
        "SUBMIT FINAL ACCUSATION",
        close_case,
        RED
    ).pack(anchor="w", pady=20)


# --------------------------------------------------
# RESTART
# --------------------------------------------------

def restart_game():
    global found_clues, questioned
    global solved_timeline, game_finished

    found_clues = set()
    questioned = set()
    solved_timeline = False
    game_finished = False

    update_status()
    show_overview()


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

def nav_button(text, command):
    make_button(
        sidebar,
        text,
        command
    ).pack(fill="x", pady=4)


nav_button("Overview", show_overview)
nav_button("Investigate", show_locations)
nav_button("Suspects", show_suspects)
nav_button("Evidence", show_evidence)
nav_button("Timeline", show_timeline)
nav_button("Final Accusation", show_accusation)

tk.Frame(sidebar, bg=PANEL).pack(fill="both", expand=True)

status_label = tk.Label(
    sidebar,
    text="EVIDENCE COLLECTED: 0 / 4",
    bg=PANEL,
    fg=GOLD,
    justify="left",
    font=("Consolas", 9, "bold"),
    wraplength=170
)
status_label.pack(anchor="w", pady=(16, 0))

# --------------------------------------------------
# START GAME
# --------------------------------------------------

show_overview()
root.mainloop()
