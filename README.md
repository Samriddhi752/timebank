# TimeBank

TimeBank is a community skill-exchange web application. Members offer skills and services, request help from other members, and exchange time credits instead of money.

## Core idea

- One hour of service equals one time credit.
- Every new member receives 3 starter credits.
- A requester sends a service request and the provider can accept or decline it.
- After the service is completed, both people confirm completion.
- Only after both confirmations does TimeBank transfer credits and create a transaction record.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Jinja templates |
| Backend | Python, Flask |
| Database | SQLite with Flask-SQLAlchemy |
| Authentication | Flask-Login |
| Password security | Werkzeug password hashing |

## Features

- User registration and login with hashed passwords
- Starter time-credit wallet
- Create, browse, search and filter service listings
- Service detail pages and exchange requests
- Provider accept / decline actions
- Requester cancellation of pending requests
- Two-sided completion confirmation
- Automatic credit transfer after both confirmations
- Transaction history for incoming and outgoing credits
- Dashboard with service, credit and request summaries
- Responsive layout for desktop and mobile screens

## Run locally (Windows PowerShell)

1. Open the project folder in VS Code.
2. Create a virtual environment (skip if the existing `venv` is already present):

   ```powershell
   python -m venv venv
   ```

3. Activate it:

   ```powershell
   venv\Scripts\activate
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Start the application:

   ```powershell
   python app.py
   ```

6. Visit `http://127.0.0.1:5000`.

The SQLite database is stored at `instance/timebank.db` and is created automatically when the app starts.

## Suggested demo flow

1. Register Account A and publish a service (for example, beginner Python tutoring).
2. Register Account B in an incognito window or a separate browser profile.
3. Account B explores the listing and sends a request.
4. Account A accepts the request from **My exchanges**.
5. Account B confirms completion; verify that neither wallet changes yet.
6. Account A confirms completion; verify that one credit is deducted from B and added to A for a one-hour service.
7. Open both wallets and verify that the transaction appears in each history.

## Database overview

- `User`: member details, password hash and current credit balance.
- `Service`: service title, category, description, duration and provider.
- `ExchangeRequest`: requester, provider, service, request status and each party's completion confirmation.
- `Transaction`: completed credit transfer, linked to one exchange. The exchange reference is unique to prevent duplicate transaction records.

## Project notes

This project is intended as an academic MVP and local demonstration. Before public deployment, add CSRF protection, stronger production configuration, rate limiting, stricter server-side input validation, and a production WSGI server. Do not use the development secret key or Flask debug mode in production.
