from typing import Any, Dict, Optional
import os

from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from psycopg import Error as PsycopgError
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from db import (
    ensure_contacts_table,
    ensure_users_table,
    execute,
    list_user_tables,
    get_table_columns,
    fetch_table_rows,
    is_valid_identifier,
    get_primary_key_columns,
)

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")


@app.route("/health", methods=["GET"])
def health() -> Any:
    return {"status": "ok"}


@app.route("/init", methods=["POST"])
def init_table() -> Any:
    try:
        ensure_contacts_table()
        return {"message": "contacts table is ready"}
    except PsycopgError as exc:
        return {"error": str(exc)}, 500


@app.route("/", methods=["GET"])
def home() -> Any:
    user_name = session.get("user_name")
    tables = []
    try:
        tables = list_user_tables()
    except PsycopgError:
        pass
    return render_template("home.html", user_name=user_name, tables=tables)


@app.route("/tables/create", methods=["POST"])
def create_table() -> Any:
    if not session.get("user_id"):
        flash("Please log in to create tables.", "error")
        return redirect(url_for("login"))

    table_name = (request.form.get("table_name") or "").strip()
    raw_cols = (request.form.get("columns") or "").strip()
    if not table_name:
        flash("Table name is required", "error")
        return redirect(url_for("home"))
    if not is_valid_identifier(table_name):
        flash("Invalid table name. Use letters, digits, underscore; start with letter/_.", "error")
        return redirect(url_for("home"))

    # Parse columns as comma-separated name:type pairs
    col_defs = []
    type_map = {
        "text": "TEXT",
        "integer": "INTEGER",
        "int": "INTEGER",
        "boolean": "BOOLEAN",
        "bool": "BOOLEAN",
        "timestamp": "TIMESTAMPTZ",
    }
    if raw_cols:
        parts = [p.strip() for p in raw_cols.split(",") if p.strip()]
        for part in parts:
            if ":" in part:
                name, typ = [x.strip() for x in part.split(":", 1)]
            else:
                name, typ = part, "text"
            if not is_valid_identifier(name):
                flash(f"Invalid column name: {name}", "error")
                return redirect(url_for("home"))
            pg_type = type_map.get(typ.lower())
            if not pg_type:
                flash(f"Unsupported type '{typ}' for column {name}", "error")
                return redirect(url_for("home"))
            col_defs.append(f"{name} {pg_type}")

    # Always include id serial PK
    columns_sql = ", ".join(["id SERIAL PRIMARY KEY"] + col_defs) if col_defs else "id SERIAL PRIMARY KEY"
    try:
        execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});")
        flash(f"Table '{table_name}' is ready.", "success")
    except PsycopgError as exc:
        flash(f"Create table failed: {exc}", "error")
    return redirect(url_for("home"))


@app.route("/tables/<table>", methods=["GET"])
def view_table(table: str) -> Any:
    if not is_valid_identifier(table):
        return {"error": "invalid table name"}, 400
    try:
        cols = get_table_columns(table)
        rows = fetch_table_rows(table, limit=200)
        pk_cols = get_primary_key_columns(table)
        pk_col = pk_cols[0] if pk_cols else None
        return render_template("table_view.html", table=table, columns=cols, rows=rows, pk_col=pk_col)
    except PsycopgError as exc:
        flash(f"Load table failed: {exc}", "error")
        return redirect(url_for("home"))


@app.route("/tables/<table>/rows", methods=["POST"])
def insert_row(table: str) -> Any:
    if not session.get("user_id"):
        flash("Please log in to modify tables.", "error")
        return redirect(url_for("login"))
    if not is_valid_identifier(table):
        flash("Invalid table name", "error")
        return redirect(url_for("home"))
    cols_meta = get_table_columns(table)
    pk_cols = get_primary_key_columns(table)
    # Build columns and params excluding PK
    insert_cols = []
    values = []
    for c in cols_meta:
        name = c["column_name"]
        if name in pk_cols:
            continue
        insert_cols.append(name)
        values.append(request.form.get(name))
    if not insert_cols:
        flash("No insertable columns", "error")
        return redirect(url_for("view_table", table=table))
    placeholders = ", ".join(["%s"] * len(insert_cols))
    cols_sql = ", ".join(insert_cols)
    try:
        execute(
            f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders});",
            values,
        )
        flash("Row inserted.", "success")
    except PsycopgError as exc:
        flash(f"Insert failed: {exc}", "error")
    return redirect(url_for("view_table", table=table))


@app.route("/tables/<table>/rows/update", methods=["POST"])
def update_row(table: str) -> Any:
    if not session.get("user_id"):
        flash("Please log in to modify tables.", "error")
        return redirect(url_for("login"))
    if not is_valid_identifier(table):
        flash("Invalid table name", "error")
        return redirect(url_for("home"))
    pk_cols = get_primary_key_columns(table)
    if not pk_cols:
        flash("Table has no primary key; cannot update", "error")
        return redirect(url_for("view_table", table=table))
    
    pk_col = pk_cols[0]
    pk_value = request.form.get(f"__pk_{pk_col}")
    if not pk_value:
        flash("Primary key value missing", "error")
        return redirect(url_for("view_table", table=table))
    
    cols_meta = get_table_columns(table)
    sets = []
    params = []
    for c in cols_meta:
        name = c["column_name"]
        if name in pk_cols:
            continue
        if name in request.form:
            sets.append(f"{name} = %s")
            params.append(request.form.get(name))
    if not sets:
        flash("Nothing to update", "info")
        return redirect(url_for("view_table", table=table))
    params.append(pk_value)
    try:
        execute(f"UPDATE {table} SET {', '.join(sets)} WHERE {pk_col} = %s;", params)
        flash("Row updated.", "success")
    except PsycopgError as exc:
        flash(f"Update failed: {exc}", "error")
    return redirect(url_for("view_table", table=table))


@app.route("/tables/<table>/rows/delete", methods=["POST"])
def delete_row(table: str) -> Any:
    if not session.get("user_id"):
        flash("Please log in to modify tables.", "error")
        return redirect(url_for("login"))
    if not is_valid_identifier(table):
        flash("Invalid table name", "error")
        return redirect(url_for("home"))
    pk_cols = get_primary_key_columns(table)
    if not pk_cols:
        flash("Table has no primary key; cannot delete", "error")
        return redirect(url_for("view_table", table=table))
    
    pk_col = pk_cols[0]
    pk_value = request.form.get(f"__pk_{pk_col}")
    if not pk_value:
        flash("Primary key value missing", "error")
        return redirect(url_for("view_table", table=table))
    
    try:
        execute(f"DELETE FROM {table} WHERE {pk_col} = %s;", [pk_value])
        flash("Row deleted.", "success")
    except PsycopgError as exc:
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
        rows = execute(
            """
            INSERT INTO users (name, password)
            VALUES (%s, %s)
            RETURNING id, name;
            """,
            [name, password_hash],
            fetch="all",
        )
        session["user_id"] = rows[0]["id"]
        session["user_name"] = rows[0]["name"]
        flash("Account created. You are now signed in.", "success")
        return redirect(url_for("home"))
    except PsycopgError as exc:
        # Likely duplicate username or DB issue
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
        rows = execute(
            """
            SELECT id, name, password
              FROM users
             WHERE name = %s
            """,
            [name],
            fetch="one",
        )
        if not rows:
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))

        user = rows[0]
        if not check_password_hash(user["password"], password):
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash("Logged in successfully.", "success")
        return redirect(url_for("home"))
    except PsycopgError as exc:
        flash(f"Login failed: {exc}", "error")
        return redirect(url_for("login"))


@app.route("/logout", methods=["POST"]) 
def logout() -> Any:
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/contacts", methods=["POST"])
def add_contact() -> Any:
    payload: Dict[str, Optional[str]] = request.get_json(force=True, silent=True) or {}
    name = payload.get("name")
    email = payload.get("email")
    if not name or not email:
        return {"error": "name and email are required"}, 400

    try:
        rows = execute(
            """
            INSERT INTO contacts (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email;
            """,
            [name, email],
            fetch="all",
        )
        return jsonify(rows[0]), 201
    except PsycopgError as exc:
        return {"error": str(exc)}, 500


@app.route("/contacts", methods=["GET"])
def list_contacts() -> Any:
    try:
        rows = execute(
            "SELECT id, name, email FROM contacts ORDER BY id;",
            fetch="all",
        )
        return jsonify(rows)
    except PsycopgError as exc:
        return {"error": str(exc)}, 500


@app.route("/contacts/<int:contact_id>", methods=["PUT"])
def update_contact(contact_id: int) -> Any:
    payload: Dict[str, Optional[str]] = request.get_json(force=True, silent=True) or {}
    name = payload.get("name")
    email = payload.get("email")
    if name is None and email is None:
        return {"error": "provide name or email to update"}, 400

    try:
        rows = execute(
            """
            UPDATE contacts
               SET name = COALESCE(%s, name),
                   email = COALESCE(%s, email)
             WHERE id = %s
         RETURNING id, name, email;
            """,
            [name, email, contact_id],
            fetch="all",
        )
        if not rows:
            return {"error": f"contact {contact_id} not found"}, 404
        return jsonify(rows[0])
    except PsycopgError as exc:
        return {"error": str(exc)}, 500


@app.route("/contacts/<int:contact_id>", methods=["DELETE"])
def delete_contact(contact_id: int) -> Any:
    try:
        rows = execute(
            """
            DELETE FROM contacts
             WHERE id = %s
         RETURNING id, name, email;
            """,
            [contact_id],
            fetch="all",
        )
        if not rows:
            return {"error": f"contact {contact_id} not found"}, 404
        return jsonify(rows[0])
    except PsycopgError as exc:
        return {"error": str(exc)}, 500


if __name__ == "__main__":
    # Ensure table exists before serving traffic.
    ensure_contacts_table()
    ensure_users_table()
    app.run(host="0.0.0.0", port=5000, debug=True)
