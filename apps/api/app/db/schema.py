"""Lightweight schema sync for local SQLite dev (create_all does not ALTER tables)."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from app.models import (  # noqa: F401 — register all models on metadata
    AgentRun,
    Card,
    Chapter,
    ChapterCommit,
    DisambiguationItem,
    Entity,
    Foreshadowing,
    Project,
    Relationship,
    ReviewIssue,
    ReviewMetric,
    SearchDoc,
    Summary,
    User,
)

logger = logging.getLogger("novelcraft.schema")


def _sqlite_add_column_if_missing(conn: Connection, table: str, column: str, col_def: str) -> None:
    """Add a column to a SQLite table if it doesn't exist.

    Args:
        conn: SQLAlchemy synchronous Connection.
        table: Table name.
        column: Column name to check/add.
        col_def: Full column definition for ALTER TABLE (e.g. 'root_dir VARCHAR(500) DEFAULT \\'\\'').
    """
    inspector = inspect(conn)
    if table not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns(table)}
    if column not in existing:
        logger.info("Migrating %s.%s: adding column", table, column)
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_def}"))
        conn.commit()


def sync_sqlite_schema(conn: Connection) -> None:
    """Apply missing columns/tables to a SQLite database.

    SQLAlchemy create_all only creates new tables; it never ALTERs existing ones.
    This function bridges that gap for local SQLite development.
    """
    if conn.dialect.name != "sqlite":
        return

    migrations = [
        # (table, column, column_definition)
        ("projects", "root_dir", "root_dir VARCHAR(500) DEFAULT ''"),
        ("projects", "synopsis_json", "synopsis_json TEXT"),
        ("chapters", "outline", "outline TEXT DEFAULT ''"),
    ]

    for table, column, col_def in migrations:
        try:
            _sqlite_add_column_if_missing(conn, table, column, col_def)
        except Exception:
            logger.exception("Migration %s.%s failed, continuing startup", table, column)
