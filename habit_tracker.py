"""Webapp to track progress on custom habits."""

from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

HABITS_FILE: str = "habits_data.json"
ACTIVITY_FILE: str = "activity_data.json"

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_dev_key')

def load_habits() -> dict:
    """Load the list of habits from a JSON file.

    Returns:
        List of habits as dictionaries.
    """
    with open(HABITS_FILE, 'r') as file:
        return json.load(file)


def load_activity() -> list:
    """Load the progress entries from a JSON file.

    Returns:
        List of progress entries as dictionaries.
    """
    with open(ACTIVITY_FILE, 'r') as file:
        return json.load(file)


def save_activity(data: list) -> None:
    """Save the progress data to a JSON file.

    Args:
        data: The progress data to save as a list of dictionaries.
    """
    with open(ACTIVITY_FILE, 'w') as file:
        json.dump(data, file, indent=4)


@app.route('/')
def home() -> str:
    """Render the home page with the list of habits.

    Returns:
        The rendered HTML of the home page.
    """
    habits = load_habits()
    return render_template('index.html', habits=habits)


@app.route('/log', methods=['POST'])
def log_habit() -> str:
    """Log a new habit entry with optional notes.

    Returns:
        A redirect to the home page.
    """
    activity = load_activity()
    new_entry = {
        "progress_id": len(activity) + 1,
        "habit_id": int(request.form.get('habit_id')),
        "date": request.form.get('date'),
        "notes": request.form.get('notes', '').strip()
    }
    activity.append(new_entry)
    save_activity(activity)
    flash("Activity logged successfully!", "success")
    return redirect(url_for('home'))


@app.route('/activity')
def show_activity_log() -> str:
    """Display filtered activity log.

    Returns:
        The rendered HTML of the activity log page.
    """
    habits = load_habits()
    activity = load_activity()
    habit_map = {habit['habit_id']: habit['habit_name'] for habit in habits}
    filter = request.args["filter"]
    log_entries = [
        {
            "date": entry['date'],
            "habit": habit_map.get(entry['habit_id'], "(unknown)"),
            "notes": entry.get('notes', '')
        }
        for entry in activity
        if filter == "all" or habit_map.get(entry['habit_id']) == filter
    ]
    return render_template('activity.html', activity=log_entries)


if __name__ == "__main__":
    app.run(host="localhost", port=5001, debug=True)

