"""Regression tests for sync_sqlite_schema — Phase 1 columns missing in Phase 0 SQLite DBs."""

import os
import sqlite3
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from app.db.schema import sync_sqlite_schema, _sqlite_add_column_if_missing


def _create_phase0_db(path: str) -> None:
    """Create a SQLite database with Phase 0 schema (no root_dir)."""
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE projects (
            id VARCHAR(36) PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            genre VARCHAR(50),
            status VARCHAR(20) DEFAULT 'active',
            owner_id VARCHAR(36) NOT NULL,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)
    conn.execute("INSERT INTO projects (id, title, owner_id) VALUES ('p1', 'Test', 'u1')")
    conn.commit()
    conn.close()


class TestSyncSqliteSchema:
    def test_adds_missing_root_dir_column(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            _create_phase0_db(db_path)

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                sync_sqlite_schema(conn)

                columns = conn.execute(text("PRAGMA table_info('projects')")).fetchall()
                col_names = {c[1] for c in columns}
                assert "root_dir" in col_names

                row = conn.execute(text("SELECT id, root_dir FROM projects WHERE id='p1'")).fetchone()
                assert row is not None
                assert row[1] == ""  # default value

            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_idempotent_second_run_does_not_fail(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            _create_phase0_db(db_path)

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                sync_sqlite_schema(conn)
                # Second run must not raise
                sync_sqlite_schema(conn)

            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_fresh_phase1_db_is_noop(self):
        """sync_sqlite_schema on a DB that already has root_dir should be a no-op."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            _create_phase0_db(db_path)
            # Manually add root_dir to simulate Phase 1 DB
            conn = sqlite3.connect(db_path)
            conn.execute("ALTER TABLE projects ADD COLUMN root_dir VARCHAR(500) DEFAULT ''")
            conn.commit()
            conn.close()

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                # Must not fail
                sync_sqlite_schema(conn)

                # Verify only one root_dir column
                columns = conn.execute(text("PRAGMA table_info('projects')")).fetchall()
                root_dir_cols = [c for c in columns if c[1] == "root_dir"]
                assert len(root_dir_cols) == 1

            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_missing_table_is_skipped(self):
        """If projects table doesn't exist, _sqlite_add_column_if_missing is a no-op."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                # Empty DB, no tables - must not raise
                _sqlite_add_column_if_missing(conn, "projects", "root_dir", "root_dir VARCHAR(500) DEFAULT ''")

            engine.dispose()
        finally:
            os.unlink(db_path)
