# Flask + MongoDB Sample

Simple Flask app with MongoDB that provides user authentication and a dashboard for managing collections and documents.

## Features
- User signup/login with password hashing
- Dashboard to create collections dynamically
- View, add, edit, and delete documents in any collection
- MongoDB-backed persistence

## Setup (Windows PowerShell)

1. **Ensure MongoDB is running** locally or accessible:
   ```powershell
   # Check if MongoDB is running
   mongosh --eval "db.version()"
   ```

2. Create a virtual environment (optional but recommended):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure environment variables (optional - defaults work for local MongoDB):
   ```powershell
   # Copy the example and edit if needed
   Copy-Item .env.example .env
   ```
   
   Default settings:
   - Host: `localhost`
   - Port: `27017`
   - Database: `Wrangling`
   - No authentication required (comment out MONGO_USER/MONGO_PASSWORD for local dev)

5. Run the app:
   ```powershell
   python app.py
   ```
   
   The server listens on http://localhost:5000

## Using the App

### Web UI
- **Home**: http://localhost:5000
- **Signup**: http://localhost:5000/signup
- **Login**: http://localhost:5000/login

### Dashboard Features
1. **Create a collection**: Enter a collection name in the dashboard. Collections are created immediately.
2. **View collections**: Click on any collection name to see its documents.
3. **Add documents**: Use the "Add Row" form to insert new documents with any fields.
4. **Edit documents**: Click in any field (except `_id`) and click "Save" to update.
5. **Delete documents**: Click "Delete" to remove a document.

## MongoDB Notes
- Collections are created dynamically when you use the dashboard.
- The `_id` field is MongoDB's default primary key (auto-generated).
- The `users` collection stores account credentials with hashed passwords.
- Fields are inferred from existing documents in the collection.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_HOST` | `localhost` | MongoDB host |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_DATABASE` | `Wrangling` | Database name |
| `MONGO_USER` | _(none)_ | Username for authentication |
| `MONGO_PASSWORD` | _(none)_ | Password for authentication |
| `FLASK_SECRET_KEY` | `dev-secret-change-me` | Session secret key |

## Differences from PostgreSQL Version
- Uses MongoDB collections instead of PostgreSQL tables
- Document-based storage (flexible schema) vs. fixed table schemas
- `_id` field instead of `id` column as primary key
- No explicit column types - MongoDB stores any JSON-like data
- Collections created on-the-fly without schema definition

## Troubleshooting
- **Connection refused**: Ensure MongoDB is running (`mongod` service).
- **Authentication failed**: Check `MONGO_USER` and `MONGO_PASSWORD` in `.env`.
- **Collection not showing fields**: Insert at least one document to infer schema.
