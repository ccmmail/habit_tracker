"""Webapp to track rolling activity and attainment on custom habits."""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
import math
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
load_dotenv()

HABITS_FILE: str = "habits_data.json"
ACTIVITY_FILE: str = "activity_data.json"
ALLOWED_EMAIL: str = "ccmmail@gmail.com"

# flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_dev_key')
app.permanent_session_lifetime = timedelta(days=90)

# OAuth Setup with Authlib
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
    api_base_url='https://openidconnect.googleapis.com/v1/'
)

def login_required(f):
    """Decorator to ensure user is logged in with allowed email."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session or session['email'] != ALLOWED_EMAIL:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


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


def get_last_update_date() -> str:
    """Return the formatted date the habits file was last modified."""
    try:
        timestamp = os.path.getmtime(HABITS_FILE)
    except FileNotFoundError:
        return "Unknown"
    return datetime.fromtimestamp(timestamp).strftime("%B %d, %Y")


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
@login_required
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
@login_required
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
@login_required
def refresh_attainment() -> str:
    """Refresh habit attainment for all habits.

    Returns:
        A redirect to the home page.
    """
    activity = load_activity()
    update_habits_activity(activity)
    flash("Goal attainment refreshed!", "success")
    return redirect(url_for('home'))


@app.route('/login')
def login():
    """Render login page or redirect to Google OAuth."""
    if 'email' in session and session['email'] == ALLOWED_EMAIL:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/authorize')
def authorize():
    """Start Google OAuth flow."""
    redirect_uri = url_for('callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/callback')
def callback():
    """Handle Google OAuth callback."""
    token = oauth.google.authorize_access_token()

    if not token:
        flash('Authentication failed', 'error')
        return redirect(url_for('login'))

    userinfo = oauth.google.get('userinfo').json()

    if userinfo.get('email') == ALLOWED_EMAIL:
        session.permanent = True
        session['email'] = userinfo.get('email')
        session['username'] = userinfo.get('name')
        flash('Successfully signed in as ' + userinfo.get('name'), 'success')
        return redirect(url_for('home'))
    else:
        flash('Unauthorized email address', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Log user out by clearing session."""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def home() -> str:
    """Render list of habits and attainment in most recent period.

    Returns:
        The rendered HTML of the home page.
    """
    habits = load_habits()
    last_update = get_last_update_date()
    return render_template('index.html', habits=habits, last_update=last_update)


if __name__ == "__main__":
    app.run(host="localhost", port=5001, debug=True)
