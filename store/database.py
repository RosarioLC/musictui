from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Self


class Database:
    """SQLite database wrapper for persistent storage.

    Creates tables for ``liked_songs`` and ``playlists`` on first connection.
    Supports use as a context manager for automatic cleanup.

    Args:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize the database connection and create tables if needed."""
        self._db_path: Path = Path(db_path)
        self._connect()

    def _connect(self) -> None:
        """Open the SQLite connection and create default tables."""
        self._conn: sqlite3.Connection = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        # Check if liked_songs exists with old schema (track_id column)
        rows = self._conn.execute("PRAGMA table_info(liked_songs)").fetchall()
        col_names = [row["name"] for row in rows]
        if "track_id" in col_names:
            # Migrate from old schema to new schema
            self._conn.execute("DROP TABLE IF EXISTS liked_songs")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS liked_songs (provider_id TEXT PRIMARY KEY)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS tracks "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "provider_id TEXT UNIQUE, title TEXT, artist TEXT, "
            "album TEXT, duration_ms INTEGER, image_path TEXT, "
            "lyrics_path TEXT, url TEXT)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS playlists "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )
        # Check if playlist_songs has a valid FK to tracks(id)
        fk_rows = self._conn.execute(
            "PRAGMA foreign_key_list(playlist_songs)"
        ).fetchall()
        has_valid_fk = any(
            row["table"] == "tracks" and row["from"] == "track_id"
            for row in fk_rows
        )
        if not has_valid_fk:
            # Recreate playlist_songs with proper FK constraint
            self._conn.execute("DROP TABLE IF EXISTS playlist_songs")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS playlist_songs "
            "(playlist_id INTEGER NOT NULL, track_id INTEGER NOT NULL, "
            "FOREIGN KEY(playlist_id) REFERENCES playlists(id), "
            "FOREIGN KEY(track_id) REFERENCES tracks(id), "
            "PRIMARY KEY(playlist_id, track_id))"
        )
        self._conn.commit()
        # Now enable foreign keys and clean up stale entries
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute(
            "DELETE FROM playlist_songs WHERE track_id NOT IN (SELECT id FROM tracks)"
        )
        self._conn.commit()

    def __enter__(self) -> Self:
        """Return self for use as a context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the database connection."""
        self.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute *query* with *params* and return the cursor.

        Args:
            query: SQL query string.
            params: Parameter tuple for query substitution.

        Returns:
            The SQLite cursor after execution.
        """
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self) -> None:
        """Commit the current transaction."""
        self._conn.commit()

    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute *query* and return all rows.

        Args:
            query: SQL query string.
            params: Parameter tuple for query substitution.

        Returns:
            A list of :class:`sqlite3.Row` objects.
        """
        return self.execute(query, params).fetchall()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
