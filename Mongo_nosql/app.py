import os
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from pymongo.errors import PyMongoError, DuplicateKeyError

from db import (
    ensure_users_collection,
    list_user_collections,
    get_collection_fields,
    fetch_collection_documents,
    is_valid_identifier,
    insert_user,
    find_user_by_name,
    insert_document,
    update_document,
    delete_document,
    get_database,
)

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")


@app.route("/health", methods=["GET"])
def health() -> Any:
    return {"status": "ok"}


@app.route("/", methods=["GET"])
def home() -> Any:
    user_name = session.get("user_name")
    collections = []
    try:
        collections = list_user_collections()
    except PyMongoError:
        pass
    return render_template("home.html", user_name=user_name, tables=collections)


@app.route("/tables/create", methods=["POST"])
def create_table() -> Any:
    if not session.get("user_id"):
        flash("Please log in to create collections.", "error")
        return redirect(url_for("login"))

    collection_name = (request.form.get("table_name") or "").strip()
    if not collection_name:
        flash("Collection name is required", "error")
        return redirect(url_for("home"))
    if not is_valid_identifier(collection_name):
        flash("Invalid collection name. Use letters, digits, underscore; start with letter/_.", "error")
        return redirect(url_for("home"))

    try:
        # In MongoDB, collections are created on first insert
        # We'll create it explicitly here
        db = get_database()
        db.create_collection(collection_name)
        flash(f"Collection '{collection_name}' is ready.", "success")
    except PyMongoError as exc:
        flash(f"Create collection failed: {exc}", "error")
    return redirect(url_for("home"))


@app.route("/tables/<table>", methods=["GET"])
def view_table(table: str) -> Any:
    if not is_valid_identifier(table):
        return {"error": "invalid collection name"}, 400
    try:
        fields = get_collection_fields(table)
        documents = fetch_collection_documents(table, limit=200)
        # _id is the primary key in MongoDB
        return render_template("table_view.html", table=table, columns=fields, rows=documents, pk_col="_id")
    except PyMongoError as exc:
        flash(f"Load collection failed: {exc}", "error")
        return redirect(url_for("home"))


@app.route("/tables/<table>/rows", methods=["POST"])
def insert_row(table: str) -> Any:
    if not session.get("user_id"):
        flash("Please log in to modify collections.", "error")
        return redirect(url_for("login"))
    if not is_valid_identifier(table):
        flash("Invalid collection name", "error")
        return redirect(url_for("home"))
    
    fields = get_collection_fields(table)
    # Build document from form data, excluding _id and processing types
    document = {}
    
    for key, value in request.form.items():
        # Skip type indicators and _id
        if key.endswith("_type") or key == "_id":
            continue
        
        # Get the type for this field
        field_type = request.form.get(f"{key}_type", "string")
        
        # Convert value based on type
        if value:
            try:
                if field_type == "number":
                    # Try int first, then float
                    try:
                        document[key] = int(value)
                    except ValueError:
                        document[key] = float(value)
                elif field_type == "boolean":
                    document[key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    document[key] = value
            except (ValueError, AttributeError):
                document[key] = value
    
    if not document:
        flash("No data to insert", "error")
        return redirect(url_for("view_table", table=table))
    
    try:
        insert_document(table, document)
        flash("Document inserted.", "success")
    except PyMongoError as exc:
        flash(f"Insert failed: {exc}", "error")
    return redirect(url_for("view_table", table=table))


@app.route("/tables/<table>/rows/update", methods=["POST"])
def update_row(table: str) -> Any:
    if not session.get("user_id"):
        flash("Please log in to modify collections.", "error")
        return redirect(url_for("login"))
    if not is_valid_identifier(table):
        flash("Invalid collection name", "error")
        return redirect(url_for("home"))
    
    doc_id = request.form.get("__pk__id")
    if not doc_id:
        flash("Document ID missing", "error")
        return redirect(url_for("view_table", table=table))
    
    # Support two update modes:
    # 1) A single `document_json` form field containing the full document as JSON
    # 2) Individual form fields per original behavior (backwards compatible)
    document_json = request.form.get("document_json")
    updates = {}
    if document_json:
        try:
            import json

            parsed = json.loads(document_json)
            # Remove _id if present - we don't allow editing it
            parsed.pop("_id", None)
            if isinstance(parsed, dict):
                updates = parsed
        except Exception:
            flash("Invalid JSON provided for update.", "error")
            return redirect(url_for("view_table", table=table))
    else:
        fields = get_collection_fields(table)
        for field in fields:
            if field == "_id":
                continue
            if field in request.form:
                updates[field] = request.form.get(field)

    if not updates:
        flash("Nothing to update", "info")
        return redirect(url_for("view_table", table=table))

    try:
        update_document(table, doc_id, updates)
        flash("Document updated.", "success")
    except PyMongoError as exc:
        flash(f"Update failed: {exc}", "error")
    return redirect(url_for("view_table", table=table))


@app.route("/tables/<table>/rows/delete", methods=["POST"])
def delete_row(table: str) -> Any:
    if not session.get("user_id"):
        flash("Please log in to modify collections.", "error")
        return redirect(url_for("login"))
    if not is_valid_identifier(table):
        flash("Invalid collection name", "error")
        return redirect(url_for("home"))
    
    doc_id = request.form.get("__pk__id")
    if not doc_id:
        flash("Document ID missing", "error")
        return redirect(url_for("view_table", table=table))
    
    try:
        delete_document(table, doc_id)
        flash("Document deleted.", "success")
    except PyMongoError as exc:
        flash(f"Delete failed: {exc}", "error")
    return redirect(url_for("view_table", table=table))


@app.route("/signup", methods=["GET", "POST"])
def signup() -> Any:
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name")
    password = request.form.get("password")
    if not name or not password:
        flash("Name and password are required", "error")
        return redirect(url_for("signup"))

    try:
        password_hash = generate_password_hash(password)
        user = insert_user(name, password_hash)
        session["user_id"] = user["_id"]
        session["user_name"] = user["name"]
        flash("Account created. You are now signed in.", "success")
        return redirect(url_for("home"))
    except DuplicateKeyError:
        flash("Username already exists", "error")
        return redirect(url_for("signup"))
    except PyMongoError as exc:
        flash(f"Signup failed: {exc}", "error")
        return redirect(url_for("signup"))


@app.route("/login", methods=["GET", "POST"])
def login() -> Any:
    if request.method == "GET":
        return render_template("login.html")

    name = request.form.get("name")
    password = request.form.get("password")
    if not name or not password:
        flash("Name and password are required", "error")
        return redirect(url_for("login"))

    try:
        user = find_user_by_name(name)
        if not user:
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["_id"]
        session["user_name"] = user["name"]
        flash("Logged in successfully.", "success")
        return redirect(url_for("home"))
    except PyMongoError as exc:
        flash(f"Login failed: {exc}", "error")
        return redirect(url_for("login"))


@app.route("/logout", methods=["POST"]) 
def logout() -> Any:
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    # Ensure users collection exists with unique index
    ensure_users_collection()
    app.run(host="0.0.0.0", port=5000, debug=True)
