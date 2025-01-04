"""Webapp to track progress on custom habits."""

from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import math
from datetime import datetime, timedelta

HABITS_FILE: str = "habits_data.json"
ACTIVITY_FILE: str = "activity_data.json"

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_dev_key')


def load_habits() -> list:
    """Load the list of habits from a JSON file.

    Returns:
        List of habits, with each habit as a dictionary.
    """
    with open(HABITS_FILE, 'r') as file:
        return json.load(file)


def save_habits(habits: list) -> None:
    """Save te habits data to a JSON file.

    Args:
        habits: list of habits, with each habit as a dictionary.
    """
    with open(HABITS_FILE, 'w') as file:
        json.dump(habits, file, indent=4)


def load_activity() -> list:
    """Load the progress entries from a JSON file.

    Returns:
        List of progress entries, with each entry a dictionary.
    """
    with open(ACTIVITY_FILE, 'r') as file:
        return json.load(file)


def save_activity(activity: list) -> None:
    """Save the progress data to a JSON file.

    Args:
        activity: List of progress entries, with each entry a dictionary.
    """
    with open(ACTIVITY_FILE, 'w') as file:
        json.dump(activity, file, indent=4)


def update_habit_activity(activity: list) -> None:
    """Update activity count within goal window for each habit.

    Args:
        activity: list of activity entries in reverse chrono order.
    """
    habits = load_habits()
    for habit in habits:
        activity_in_period, goal_attainment = count_habit_activity(habit, activity)
        habit["activity_in_period"] = activity_in_period
        habit["goal_attainment"] = goal_attainment
    save_habits(habits)


def count_habit_activity(habit: dict, activity: list) -> tuple:
    """Count activity and goal attainment of given habit within time period.

    Args:
        habit: dictionary of habit to be counted.
        activity: list of activity entries in reverse chrono order.

    Returns:
        Tuple of count of habit activity and integer of goal attainment.
    """
    count = 0
    start_window = datetime.now() - timedelta(days=habit["goal_period"])
    for entry in activity:
        if datetime.strptime(entry["date"], "%Y-%m-%d") > start_window:
            if entry["habit_id"] == habit["habit_id"]:
                count += 1
        else:
            break
    goal_attainment = math.ceil(count / habit["goal_activity"] * 100)
    return count, goal_attainment


@app.route('/log', methods=['POST'])
def log_habit() -> str:
    """Log habit entry in reverse chrono order and update habit progress.

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
    if (datetime.strptime(new_entry["date"], "%Y-%m-%d") <
            datetime.strptime(activity[0]["date"], "%Y-%m-%d")):
        activity.insert(0, new_entry)
        activity.sort(key=lambda x: x['date'], reverse=True)
    else:
        activity.insert(0, new_entry)
    save_activity(activity)
    flash("Activity logged successfully!", "success")
    update_habit_activity(activity)
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
    activity_filter = request.args["filter"]
    filtered_activity = [
        {
            "date": entry['date'],
            "habit": habit_map.get(entry['habit_id'], "(unknown)"),
            "notes": entry.get('notes', '')
        }
        for entry in activity
        if activity_filter == "all" or habit_map.get(entry['habit_id']) == activity_filter
    ]
    return render_template('activity.html', activity=filtered_activity)


@app.route('/')
def home() -> str:
    """Render the home page with the list of habits.

    Returns:
        The rendered HTML of the home page.
    """
    habits = load_habits()
    return render_template('index.html', habits=habits)


if __name__ == "__main__":
    app.run(host="localhost", port=5001, debug=True)
