# Repository Guidelines

## Project Structure & Module Organization
Source lives in `habit_tracker.py`, which wires Flask routes, Google OAuth, and JSON storage. Configuration, secrets, and session keys are loaded from `.env`. Static data is persisted in `habits_data.json` and `activity_data.json`; keep them in reverse-chronological order as the code expects. Templates under `templates/` (`index.html`, `activity.html`, `login.html`) define the UI and rely on Jinja auto-escaping. There are no dedicated test or asset directories; create new modules under the repo root or in a `tests/` directory if needed.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create/use a virtualenv for isolated dependencies.
- `pip install -r requirements.txt`: install Flask, Authlib, python-dotenv, and other runtime needs.
- `cp .env.example .env` (if provided) or `touch .env`: create the config file with `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `ALLOWED_EMAIL`.
- `python habit_tracker.py`: run the server on `localhost:5001`; ensure OAuth credentials allow that redirect URI.

## Coding Style & Naming Conventions
Use Python 3.10+ features (type hints, f-strings). Follow PEP 8 (4-space indents, snake_case for variables/functions, CapWords for classes). Keep helper functions small and documented; docstrings already follow the Google-style summary. Favor descriptive names like `count_habit_activity` and avoid abbreviations. Keep templates tidy, and ensure any new Jinja variables are escaped by default.

## Testing Guidelines
The project currently lacks automated tests. When adding them, prefer `pytest` with tests under `tests/` mirroring the module structure (e.g., `tests/test_habit_tracker.py`). Name tests after the behavior (`test_refresh_updates_attainment`). Until automated tests exist, verify flows manually: 1) load `/login`, 2) complete OAuth, 3) log a habit entry, 4) confirm `/activity?filter=all` renders without errors.

## Commit & Pull Request Guidelines
Recent commits (`git log`) are short, action-oriented messages (“fixed security issues with flask configuration”). Keep future commits concise, imperative, and scoped to a single concern. Pull requests should describe motivation, summarize changes, note config/env updates, and include screenshots for UI adjustments. Link issues when available and list manual test steps so reviewers can confirm behavior quickly.

## Security & Configuration Tips
Never commit real `.env` contents—use examples or placeholders. Validate any new routes with `@login_required` when they expose habit data. When extending persistence, sanitize user input before writing to JSON and ensure templates continue to escape injected strings to avoid XSS.
