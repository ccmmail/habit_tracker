"""Interactive app to track progress on habits."""

import json
from datetime import date

HABITS_FILE = "habits_data.json"
ACTIVITY_FILE = "activity_data.json"
NAME = "Chung"


def load_habits() -> dict:
    """Load list of habits from local file."""
    with open(HABITS_FILE, 'r') as file:
        data = json.load(file)
    return data


def present_habits(habits: dict):
    """Display list of habits being worked on."""
    print("These are your habits!")
    for index, habit in enumerate(habits):
        print(f"{index+1}. {habit['name']} -- {habit['goal']} times per {habit['frequency']}")
    print("8: show all activity")
    print("9: exit")


def log_activity(habit_id: int, notes=None):
    """Timestamp and Log a specific activity into local file."""
    with open(ACTIVITY_FILE, "r+") as file:
        data = json.load(file)
        new_entry = {"progress_id": len(data) + 1
                     "habit_id": habit_id,
                     "date": date.today().strftime("%Y-%m-%d"),
                     "notes": notes
                     }
        data.append(new_entry)
        file.seek(0)
        json.dump(data, file, indent=4)


def activity_log(habits: dict):
    """Show the log of all activity to date."""
    with open(ACTIVITY_FILE, "r") as file:
        data = json.load(file)
        print("Activity log:")
        for entry in data:
            habit_index = entry['habit_id'] - 1
            print(f"{entry['date']} - {habits[habit_index]['name']} - {entry['notes']}")

def main():
    """Present and process user choices."""
    habits = load_habits()
    while True:
        present_habits(habits)
        habit_id = int(input("Which habit did we work on today? "))
        if habit_id < 8:
            notes = input("Anything to note? ")
            log_activity(habit_id, notes)
        elif habit_id == 8:
            activity_log(habits)
        elif habit_id == 9:
            break



if __name__ == "__main__":
    main()
