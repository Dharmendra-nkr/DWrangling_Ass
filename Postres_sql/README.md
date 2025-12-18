# Flask + Postgres sample

Simple Flask app that connects to your Postgres database `Wrangling` (user `postgres`) and manipulates a `contacts` table.

## Setup (Windows PowerShell)

1. Create a virtualenv (optional but recommended):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Configure environment variables (adjust host/port/password as needed):
   ```powershell
   $Env:PGHOST="localhost"
   $Env:PGPORT="5432"
   $Env:PGUSER="postgres"
   $Env:PGPASSWORD="<your_password>"
   $Env:PGDATABASE="Wrangling"
   ```
   You can copy `.env.example` to `.env` and load it with `python -m dotenv run -- python app.py` if you prefer.

## Run the app

```powershell
python app.py
```
The server listens on http://localhost:5000.

### Web UI (Signup/Login)

- Visit http://localhost:5000 to see the home page.
- Create an account at http://localhost:5000/signup (stored in `users` table: `id`, `name`, `password` hash).
- Log in at http://localhost:5000/login. A session cookie keeps you signed in. Use the Logout button in the header to sign out.

## API quickstart

1. Initialize the table (idempotent):
   ```powershell
   Invoke-RestMethod -Method Post http://localhost:5000/init
   ```
2. Add a contact:
   ```powershell
   Invoke-RestMethod -Method Post http://localhost:5000/contacts -Body (@{name="Ada"; email="ada@example.com"} | ConvertTo-Json) -ContentType "application/json"
   ```
3. List contacts:
   ```powershell
   Invoke-RestMethod -Method Get http://localhost:5000/contacts
   ```
4. Update a contact:
   ```powershell
   Invoke-RestMethod -Method Put http://localhost:5000/contacts/1 -Body (@{email="ada.l@example.com"} | ConvertTo-Json) -ContentType "application/json"
   ```
5. Delete a contact:
   ```powershell
   Invoke-RestMethod -Method Delete http://localhost:5000/contacts/1
   ```

## Notes
- The DB name defaults to `Wrangling` and user to `postgres` per your request.
- If you see connection errors, verify host/port and that Postgres accepts TCP connections.
- The app auto-creates the `contacts` table on startup or when you POST to `/init`.
- The app also auto-creates a `users` table on startup for the web UI. Passwords are hashed via Werkzeug and stored in the `password` column.
- If `psycopg2-binary` previously failed to build on Python 3.13/Windows, this project now uses `psycopg[binary]` which installs prebuilt wheels.
