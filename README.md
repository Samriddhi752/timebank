# TimeBank

A community platform where people exchange skills and services using time credits instead of money.

## Tech stack
- Python + Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- HTML, CSS and JavaScript

## Run locally

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the application:
   ```bash
   python app.py
   ```

4. Open http://127.0.0.1:5000

The SQLite database is created automatically in `instance/timebank.db`.

## Current starter features
- Signup and login with hashed passwords
- Three starter credits for new accounts
- User dashboard
- Create and browse service listings
- Search and category filtering

## Next implementation milestone
- Exchange request model and workflow
- Provider accept/reject actions
- Dual completion confirmation
- Atomic credit transfer and transaction history

## Important
This is a development starter. Before public deployment, set a strong `SECRET_KEY`, add CSRF protection, validate redirects and permissions, and use production-safe server settings.