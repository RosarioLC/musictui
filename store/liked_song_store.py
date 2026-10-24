from model.track import Track
from store.database import Database


class LikedSongStore:
    """Persists liked songs to the database."""

    def __init__(self, db: Database) -> None:
        """Initialize the store.

        Args:
            db: Database connection.
        """
        self._db: Database = db

    def add(self, track: Track) -> None:
        """Add a track to the liked songs collection.

        Args:
            track: The track to like.
        """
        self._db.execute(
            "INSERT OR IGNORE INTO liked_songs (provider_id) VALUES (?)",
            (track.provider_id,),
        )
        self._db.commit()

    def remove(self, track: Track) -> None:
        """Remove a track from the liked songs collection.

        Args:
            track: The track to unlike.
        """
        self._db.execute(
            "DELETE FROM liked_songs WHERE provider_id = ?", (track.provider_id,)
        )
        self._db.commit()

    def list_ids(self) -> list[str]:
        """Return a list of all liked provider IDs, ordered by ID.

        Returns:
            List of provider ID strings.
        """
        rows = self._db.fetchall(
            "SELECT provider_id FROM liked_songs ORDER BY provider_id"
        )
        return [row["provider_id"] for row in rows]
