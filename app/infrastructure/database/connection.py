"""
Database connection manager.
Provides sqlite3 connections with row_factory = sqlite3.Row.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager


class ConnectionManager:
    """Manages SQLite database connections."""

    def __init__(self, db_path: Path):
        self._db_path = db_path

    @property
    def db_path(self) -> Path:
        return self._db_path

    @contextmanager
    def connection(self):
        """Get a database connection (context manager)."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
