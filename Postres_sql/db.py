import os
from typing import Any, Dict, Iterable, Optional, Sequence

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
import re


# Load environment variables from a local .env file if present.
load_dotenv()


DEFAULT_DB_CONFIG: Dict[str, Any] = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": None,
    "dbname": "Wrangling",
}


def get_db_config() -> Dict[str, Any]:
    """Collect connection settings from environment variables with sane defaults."""
    return {
        "host": os.getenv("PGHOST", DEFAULT_DB_CONFIG["host"]),
        "port": int(os.getenv("PGPORT", DEFAULT_DB_CONFIG["port"])),
        "user": os.getenv("PGUSER", DEFAULT_DB_CONFIG["user"]),
        "password": os.getenv("PGPASSWORD", DEFAULT_DB_CONFIG["password"]),
        "dbname": os.getenv("PGDATABASE", DEFAULT_DB_CONFIG["dbname"]),
    }


def get_connection():
    """Return a psycopg connection using current environment; autocommit enabled."""
    config = get_db_config()
    conn = psycopg.connect(**config)
    conn.autocommit = True
    return conn


def ensure_contacts_table() -> None:
    """Create a simple contacts table if it does not already exist."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE
    );
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(create_sql)


def ensure_users_table() -> None:
    """Create a simple users table if it does not already exist.

    The table stores a username and a password hash. The column is named
    `password` as requested, but values should be hashed (not plain text).
    """
    create_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(create_sql)


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_identifier(name: str) -> bool:
    return bool(_IDENT_RE.match(name))


def list_user_tables() -> Sequence[str]:
    """Return user tables in public schema (excluding pg/internal schemas)."""
    query = (
        """
        SELECT table_name
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_type = 'BASE TABLE'
         ORDER BY table_name;
        """
    )
    rows = execute(query, fetch="all") or []
    return [r["table_name"] for r in rows]  # type: ignore[index]


def get_table_columns(table_name: str) -> Sequence[Dict[str, Any]]:
    """Return column metadata for a table in public schema."""
    if not is_valid_identifier(table_name):
        raise ValueError("invalid table name")
    rows = execute(
        """
        SELECT column_name, data_type, is_nullable
          FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = %s
         ORDER BY ordinal_position;
        """,
        [table_name],
        fetch="all",
    )
    return rows or []


def get_primary_key_columns(table_name: str) -> Sequence[str]:
    """Return the primary key column(s) for a table."""
    if not is_valid_identifier(table_name):
        raise ValueError("invalid table name")
    rows = execute(
        """
        SELECT a.attname
          FROM pg_index i
          JOIN pg_attribute a ON a.attrelid = i.indrelid
             AND a.attnum = ANY(i.indkey)
         WHERE i.indisprimary
           AND i.indrelid = %s::regclass
         ORDER BY a.attnum;
        """,
        [table_name],
        fetch="all",
    )
    return [r["attname"] for r in (rows or [])]  # type: ignore[index]


def fetch_table_rows(table_name: str, limit: int = 100) -> Sequence[Dict[str, Any]]:
    if not is_valid_identifier(table_name):
        raise ValueError("invalid table name")
    query = f"SELECT * FROM {table_name} ORDER BY 1 LIMIT %s;"
    rows = execute(query, [limit], fetch="all")
    return rows or []


def execute(  # type: ignore[override]
    query: str,
    params: Optional[Sequence[Any]] = None,
    fetch: Optional[str] = None,
) -> Optional[Iterable[Dict[str, Any]]]:
    """Execute a query and optionally fetch rows as dicts."""
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        if fetch == "one":
            row = cur.fetchone()
            return [row] if row else []
        if fetch == "all":
            return cur.fetchall()
        return None
