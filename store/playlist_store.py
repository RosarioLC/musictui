
from catalog.catalog_source import CatalogSource
from model.playlist import Playlist
from model.track import Track
from store.database import Database


class PlaylistStore:
    """Persists playlists to the database."""

    LIKED_SONGS_ID: int = -1  # Reserved ID for the special "Liked Songs" playlist

    def __init__(
        self,
        db: Database,
        catalog: CatalogSource | None = None,
    ) -> None:
        """Initialize the store.

        Args:
            db: Database connection.
            catalog: Optional catalog source for resolving track IDs to Track objects.
        """
        self._db: Database = db
        self._catalog: CatalogSource | None = catalog
        self._ensure_liked_songs_playlist()

    def _ensure_liked_songs_playlist(self) -> None:
        """Ensure the default 'Liked Songs' playlist exists."""
        rows = self._db.fetchall(
            "SELECT id FROM playlists WHERE name = 'Liked Songs' LIMIT 1"
        )
        if not rows:
            self._db.execute(
                "INSERT INTO playlists (id, name) VALUES (?, ?)",
                (self.LIKED_SONGS_ID, "Liked Songs"),
            )
            self._db.commit()

    def _resolve_tracks(self, track_ids: list[int]) -> list[Track]:
        """Resolve a list of track IDs to Track objects from the database."""
        tracks = []
        for tid in track_ids:
            track = self._get_track_from_db(tid)
            if track:
                tracks.append(track)
        return tracks

    def _get_track_from_db(self, identifier: int | str) -> Track | None:
        """Get a track from the database by ID or provider_id."""
        if isinstance(identifier, str):
            row = self._db.execute(
                "SELECT * FROM tracks WHERE provider_id = ?", (identifier,)
            ).fetchone()
        else:
            row = self._db.execute(
                "SELECT * FROM tracks WHERE id = ?", (identifier,)
            ).fetchone()
        if row is None:
            return None
        return Track(
            id=row["id"],
            title=row["title"],
            artist=row["artist"],
            album=row["album"],
            duration_ms=row["duration_ms"],
            image_path=row["image_path"],
            lyrics_path=row["lyrics_path"],
            url=row["url"],
            provider_id=row["provider_id"],
        )

    def _store_track(self, track: Track) -> None:
        """Store a track in the database."""
        self._db.execute(
            """INSERT OR REPLACE INTO tracks 
               (provider_id, title, artist, album, duration_ms, image_path, lyrics_path, url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                track.provider_id,
                track.title,
                track.artist,
                track.album,
                track.duration_ms,
                track.image_path,
                track.lyrics_path,
                track.url,
            ),
        )
        self._db.commit()

    def _get_track_ids_for_playlist(self, playlist_id: int) -> list[int]:
        """Get the track IDs for a playlist from the database."""
        rows = self._db.fetchall(
            "SELECT track_id FROM playlist_songs WHERE playlist_id = ? ORDER BY track_id",
            (playlist_id,),
        )
        return [row["track_id"] for row in rows]

    def create(self, name: str) -> Playlist:
        """Create a new playlist and return it."""
        cursor = self._db.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
        self._db.commit()
        playlist_id = cursor.lastrowid
        if playlist_id is None:
            raise RuntimeError("Database did not return the new playlist ID")
        track_ids = self._get_track_ids_for_playlist(playlist_id)
        songs = self._resolve_tracks(track_ids)
        return Playlist(id=playlist_id, name=name, songs=songs)

    def rename(self, playlist_id: int, new_name: str) -> None:
        """Rename a playlist."""
        cursor = self._db.execute(
            "SELECT id FROM playlists WHERE id = ?", (playlist_id,)
        )
        if cursor.fetchone() is None:
            raise ValueError(f"Playlist with ID {playlist_id} does not exist")
        self._db.execute(
            "UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist_id)
        )
        self._db.commit()

    def delete(self, playlist_id: int) -> None:
        """Delete a playlist by ID."""
        self._db.execute(
            "DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,)
        )
        self._db.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        self._db.commit()

    def add_song(self, playlist_id: int, track: Track) -> None:
        """Add a song to a playlist."""
        if not track.provider_id:
            raise ValueError("Track has no provider_id")
        # Ensure the track is stored in the database and get its DB id
        existing = self._get_track_from_db(track.provider_id)
        if existing is None:
            self._store_track(track)
        # Look up the actual DB id (may differ from in-memory track.id)
        row = self._db.execute(
            "SELECT id FROM tracks WHERE provider_id = ?", (track.provider_id,)
        ).fetchone()
        db_track_id = row["id"] if row else track.id
        if db_track_id is None:
            raise ValueError("Could not resolve track in database")
        # Check if already in playlist
        rows = self._db.fetchall(
            "SELECT 1 FROM playlist_songs WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, db_track_id),
        )
        if rows:
            raise ValueError("Track is already in this playlist")
        self._db.execute(
            "INSERT INTO playlist_songs (playlist_id, track_id) VALUES (?, ?)",
            (playlist_id, db_track_id),
        )
        self._db.commit()

    def remove_song(self, playlist_id: int, track: Track) -> None:
        """Remove a song from a playlist."""
        if not track.provider_id:
            raise ValueError("Track has no provider_id")
        # Resolve the actual DB track id
        row = self._db.execute(
            "SELECT id FROM tracks WHERE provider_id = ?", (track.provider_id,)
        ).fetchone()
        db_track_id = row["id"] if row else track.id
        cursor = self._db.execute(
            "SELECT 1 FROM playlist_songs WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, db_track_id),
        )
        if cursor.fetchone() is None:
            raise ValueError("Track is not in this playlist")
        self._db.execute(
            "DELETE FROM playlist_songs WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, db_track_id),
        )
        self._db.commit()

    def list(self) -> list[Playlist]:
        """Return all playlists ordered by name."""
        rows = self._db.fetchall("SELECT id, name FROM playlists ORDER BY name")
        playlists = []
        for row in rows:
            playlist_id = row["id"]
            name = row["name"]
            track_ids = self._get_track_ids_for_playlist(playlist_id)
            songs = self._resolve_tracks(track_ids)
            playlists.append(Playlist(id=playlist_id, name=name, songs=songs))
        return playlists

    def get_liked_songs(self) -> list[Track]:
        """Get all liked songs from the liked_songs table.

        Returns:
            List of Track objects for all liked songs.
        """
        rows = self._db.fetchall(
            "SELECT * FROM tracks WHERE provider_id IN (SELECT provider_id FROM liked_songs) ORDER BY id"
        )
        tracks = []
        for row in rows:
            tracks.append(
                Track(
                    id=row["id"],
                    title=row["title"],
                    artist=row["artist"],
                    album=row["album"],
                    duration_ms=row["duration_ms"],
                    image_path=row["image_path"],
                    lyrics_path=row["lyrics_path"],
                    url=row["url"],
                    provider_id=row["provider_id"],
                )
            )
        return tracks

    def _get_liked_track_ids(self) -> list[int]:
        """Get all liked track IDs from the database."""
        rows = self._db.fetchall(
            "SELECT id FROM tracks WHERE provider_id IN (SELECT provider_id FROM liked_songs) ORDER BY id"
        )
        return [row["id"] for row in rows]

    def add_to_liked_songs(self, track: Track) -> None:
        """Add a track to the liked songs collection."""
        # Ensure the track is stored in the database
        existing = self._get_track_from_db(track.provider_id)
        if existing is None:
            self._store_track(track)
        self._db.execute(
            "INSERT OR IGNORE INTO liked_songs (provider_id) VALUES (?)",
            (track.provider_id,),
        )
        self._db.commit()

    def remove_from_liked_songs(self, track: Track) -> None:
        """Remove a track from the liked songs collection."""
        self._db.execute(
            "DELETE FROM liked_songs WHERE provider_id = ?", (track.provider_id,)
        )
        self._db.commit()

    def is_liked(self, track: Track) -> bool:
        """Check if a track is in the liked songs collection."""
        rows = self._db.fetchall(
            "SELECT 1 FROM liked_songs WHERE provider_id = ? LIMIT 1",
            (track.provider_id,),
        )
        return len(rows) > 0
