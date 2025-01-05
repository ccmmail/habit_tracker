"""Webapp to track rolling activity and attainment on custom habits."""

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
    """Save habits data to a JSON file.

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
        activity: List of activity entries, with each entry a dictionary.
    """
    with open(ACTIVITY_FILE, 'w') as file:
        json.dump(activity, file, indent=4)


def update_habits_activity(activity: list) -> None:
    """Update activity count and attainment percentage for all habits.

    Args:
        activity: list of activity entries in reverse chrono order.
    """
    habits = load_habits()
    for habit in habits:
        habit.update(count_habit_activity(habit, activity))
    save_habits(habits)


def count_habit_activity(habit: dict, activity: list) -> dict:
    """Count activity and goal attainment of given habit within time period.

    Args:
        habit: dictionary of habit to be counted from activity list.
        activity: list of activity entries in reverse chrono order.

    Returns:
        habit dictionary updated with count of habit activity and
        integer of goal attainment.
    """
    habit["period_minus_one_activity"] = 0
    habit["period_minus_one_attainment"] = 0
    habit["period_minus_two_activity"] = 0
    habit["period_minus_two_attainment"] = 0
    habit["period_minus_three_activity"] = 0
    habit["period_minus_three_attainment"] = 0
    habit["period_minus_four_activity"] = 0
    habit["period_minus_four_attainment"] = 0
    end_period = datetime.now()
    start_period_minus_one = datetime.now() - timedelta(days=habit["goal_period"])
    start_period_minus_two = datetime.now() - timedelta(days=habit["goal_period"] * 2)
    start_period_minus_three = datetime.now() - timedelta(days=habit["goal_period"] * 3)
    start_period_minus_four = datetime.now() - timedelta(days=habit["goal_period"] * 4)
    for entry in activity:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
        if start_period_minus_one < entry_date <= end_period:
            if entry["habit_id"] == habit["habit_id"]:
                habit["period_minus_one_activity"] += 1
        if start_period_minus_two < entry_date <= start_period_minus_one:
            if entry["habit_id"] == habit["habit_id"]:
                habit["period_minus_two_activity"] += 1
        if start_period_minus_three < entry_date <= start_period_minus_two:
            if entry["habit_id"] == habit["habit_id"]:
                habit["period_minus_three_activity"] += 1
        if start_period_minus_four < entry_date <= start_period_minus_three:
            if entry["habit_id"] == habit["habit_id"]:
                habit["period_minus_four_activity"] += 1
        if entry_date <= start_period_minus_three:
            break
    habit["period_minus_one_attainment"] = math.ceil(habit["period_minus_one_activity"]
                                                     / habit["goal_target"] * 100)
    habit["period_minus_two_attainment"] = math.ceil(habit["period_minus_two_activity"]
                                                     / habit["goal_target"] * 100)
    habit["period_minus_three_attainment"] = math.ceil(habit["period_minus_three_activity"]
                                                       / habit["goal_target"] * 100)
    habit["period_minus_four_attainment"] = math.ceil(habit["period_minus_four_activity"]
                                                       / habit["goal_target"] * 100)
    return habit


@app.route('/log', methods=['POST'])
def log_habit() -> str:
    """Log habit entry in reverse chrono order and update habit attainment.

    Args:
        habit_id: integer ID of habit to log (from POST).
        date: string date of habit entry (from POST).
        notes: optional string notes of habit entry (from POST).

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
    flash("Activity logged!", "success")
    update_habits_activity(activity)
    return redirect(url_for('home'))


@app.route('/activity')
def show_activity_log() -> str:
    """Display attainment by period and filtered activity log.

    Args:
        filter: habit name to filter activity log (from GET).

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
    return render_template('activity.html', activity=filtered_activity, habits=habits)


@app.route('/refresh')
def refresh_attainment() -> str:
    """Refresh habit attainment for all habits.

    Returns:
        A redirect to the home page.
    """
    activity = load_activity()
    update_habits_activity(activity)
    flash("Goal attainment refreshed!", "success")
    return redirect(url_for('home'))


@app.route('/')
def home() -> str:
    """Render list of habits and attainment in most recent period.

    Returns:
        The rendered HTML of the home page.
    """
    habits = load_habits()
    return render_template('index.html', habits=habits)


if __name__ == "__main__":
    app.run(host="localhost", port=5001, debug=True)
