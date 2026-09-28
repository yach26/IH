"""
Database abstraction layer for AgroTwin AI.
Supports both SQLite (local development, fast tests) and PostgreSQL / NeonDB (production).
Switched automatically via DATABASE_URL environment variable.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from typing import Any, Iterator, Optional

DATABASE_URL = os.environ.get("DATABASE_URL")
AGROTWIN_DB = os.environ.get(
    "AGROTWIN_DB",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrotwin.db")),
)


def _json_load(value: Any, default: Any = None) -> Any:
    """Safe JSON loader that works for both backends:
    - SQLite stores JSON as TEXT → value is str, needs json.loads()
    - PostgreSQL JSONB → psycopg3 auto-deserializes to dict/list, already parsed.
    Returns `default` when value is None/empty.
    """
    if value is None:
        return default if default is not None else {}
    if isinstance(value, (dict, list)):
        return value          # already deserialized by psycopg3
    if isinstance(value, (str, bytes, bytearray)):
        return json.loads(value) if value else (default if default is not None else {})
    return value              # unexpected type — pass through


SCHEMA_SQLITE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "schema_sqlite.sql")
)
SCHEMA_POSTGRES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "schema_postgres.sql")
)

TABLE_PKS = {
    "regions": "region_id",
    "districts": "district_id",
    "talukas": "taluka_id",
    "farmers": "farmer_id",
    "fields": "field_id",
    "crops": "crop_id",
    "crop_calendars": "calendar_id",
    "field_crops": "field_crop_id",
    "fertilizer_products": "product_id",
    "fertilizer_recommendations": "rec_id",
    "soil_tests": "soil_test_id",
    "applications": "application_id",
    "nutrient_ledger_entries": "ledger_id",
    "recommendations": "recommendation_id",
    "weather_snapshots": "snapshot_id",
    "events": "event_id",
    "alerts": "alert_id",
    "audit_log": "audit_id",
    "soil_report_uploads": "upload_id",
}


def is_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


def translate_sqlite_to_pg(sql: str) -> tuple[str, Optional[str]]:
    """Translates SQLite query syntax to PostgreSQL."""
    clean_sql = sql.strip()
    if clean_sql.upper().startswith("PRAGMA"):
        return "-- pragma ignored in pg", None

    pg_sql = clean_sql.replace("?", "%s")
    pk_col = None

    insert_match = re.match(r"^\s*INSERT\s+INTO\s+([a-zA-Z0-9_]+)", clean_sql, re.IGNORECASE)
    if insert_match and "RETURNING" not in clean_sql.upper():
        tbl = insert_match.group(1).lower()
        if tbl in TABLE_PKS:
            pk_col = TABLE_PKS[tbl]
            pg_sql = f"{pg_sql.rstrip(';')} RETURNING {pk_col}"

    return pg_sql, pk_col


class PostgresCursorWrapper:
    def __init__(self, pg_cursor):
        self._cur = pg_cursor
        self.lastrowid: Any = None

    def execute(self, sql: str, params: Any = None):
        pg_sql, pk_col = translate_sqlite_to_pg(sql)
        if pg_sql.startswith("-- pragma"):
            return self

        if params is not None:
            self._cur.execute(pg_sql, tuple(params) if isinstance(params, (list, tuple)) else params)
        else:
            self._cur.execute(pg_sql)

        if pk_col and self._cur.description:
            try:
                row = self._cur.fetchone()
                if row:
                    self.lastrowid = row[pk_col] if isinstance(row, dict) else row[0]
            except Exception:
                self.lastrowid = None
        else:
            self.lastrowid = None
        return self

    def executemany(self, sql: str, seq_of_params: Any):
        pg_sql, _ = translate_sqlite_to_pg(sql)
        self._cur.executemany(pg_sql, seq_of_params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def close(self):
        self._cur.close()

    def __iter__(self):
        return iter(self._cur)


class PostgresConnectionWrapper:
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor())

    def execute(self, sql: str, params: Any = None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def executescript(self, script: str):
        with self._conn.cursor() as cur:
            cur.execute(script)
        self._conn.commit()


def get_db_connection() -> Any:
    """Returns an active database connection (SQLite or PostgreSQL)."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        try:
            import psycopg
            from psycopg.rows import dict_row

            conn = psycopg.connect(db_url, row_factory=dict_row)
            return PostgresConnectionWrapper(conn)
        except ImportError as e:
            raise ImportError(
                "psycopg is required when DATABASE_URL is set. Run: pip install psycopg[binary]"
            ) from e
    else:
        conn = sqlite3.connect(os.environ.get("AGROTWIN_DB", AGROTWIN_DB), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def init_db(conn: Any = None) -> None:
    """Initializes tables using schema_postgres.sql or schema_sqlite.sql."""
    close_after = False
    if conn is None:
        conn = get_db_connection()
        close_after = True

    try:
        if is_postgres():
            with open(SCHEMA_POSTGRES_PATH, "r", encoding="utf-8") as f:
                ddl = f.read()
            conn.executescript(ddl)
        else:
            with open(SCHEMA_SQLITE_PATH, "r", encoding="utf-8") as f:
                ddl = f.read()
            conn.executescript(ddl)
    finally:
        if close_after:
            conn.close()
