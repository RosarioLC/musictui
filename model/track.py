"""Track model representing a single music track."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as _dc_replace

# Module-level constants for default values.
# Using constants instead of a shared dict avoids accidental mutation.
_DEFAULT_TITLE: str = "Unknown Title"
_DEFAULT_ARTIST: str = "Unknown Artist"
_DEFAULT_ALBUM: str = "Unknown Album"
_DEFAULT_IMAGE_PATH: str = "Unknown Image Path"
_DEFAULT_LYRICS_PATH: str = "Unknown Lyrics Path"
_DEFAULT_URL: str = ""


@dataclass(slots=True, frozen=True)
class Track:
    """Immutable representation of a single music track with full metadata.

    Tracks are effectively immutable: all fields are validated and normalized
    at construction time via :meth:`__post_init__`.  Empty or whitespace-only
    string fields are replaced with sensible defaults.  The :meth:`replace`
    method supports functional-style updates by producing a new :class:`Track`
    with selected fields changed.

    Tracks are hashable by ID, making them suitable for use in sets and as
    dictionary keys.  Equality is determined solely by the ``id`` field.

    Attributes:
        id: Unique integer identifier for this track within the application.
        title: The track's display title. Defaults to ``"Unknown Title"``.
        artist: The primary artist name. Defaults to ``"Unknown Artist"``.
        album: The parent album name. Defaults to ``"Unknown Album"``.
        duration_ms: Total duration in milliseconds. Clamped to zero if negative.
        image_path: File path or URL for album artwork. Defaults to
            ``"Unknown Image Path"``.
        lyrics_path: File path for local LRC lyrics. Defaults to
            ``"Unknown Lyrics Path"``.
        url: Playable URL (e.g. YouTube Music watch URL). Defaults to empty
            string.
        provider_id: External provider identifier (e.g. YouTube video ID).
            Defaults to empty string.
    """

    id: int
    title: str = _DEFAULT_TITLE
    artist: str = _DEFAULT_ARTIST
    album: str = _DEFAULT_ALBUM
    duration_ms: int = 0
    image_path: str = _DEFAULT_IMAGE_PATH
    lyrics_path: str = _DEFAULT_LYRICS_PATH
    url: str = _DEFAULT_URL
    provider_id: str = ""

    def __post_init__(self) -> None:
        """Normalize empty or whitespace-only fields to defaults.

        Uses :func:`object.__setattr__` because the dataclass uses slots
        (but is not frozen).  Also clamps ``duration_ms`` to non-negative.
        """
        if not self.title or not self.title.strip():
            object.__setattr__(self, "title", _DEFAULT_TITLE)
        if not self.artist or not self.artist.strip():
            object.__setattr__(self, "artist", _DEFAULT_ARTIST)
        if not self.album or not self.album.strip():
            object.__setattr__(self, "album", _DEFAULT_ALBUM)
        if not self.image_path or not self.image_path.strip():
            object.__setattr__(self, "image_path", _DEFAULT_IMAGE_PATH)
        if not self.lyrics_path or not self.lyrics_path.strip():
            object.__setattr__(self, "lyrics_path", _DEFAULT_LYRICS_PATH)
        if not self.url or not self.url.strip():
            object.__setattr__(self, "url", _DEFAULT_URL)
        if self.duration_ms < 0:
            object.__setattr__(self, "duration_ms", 0)

    def to_dict(self) -> dict[str, object]:
        """Serialize the track to a plain dictionary suitable for storage.

        Returns:
            A dictionary mapping each attribute name to its current value.
        """
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration_ms": self.duration_ms,
            "lyrics_path": self.lyrics_path,
            "url": self.url,
            "provider_id": self.provider_id,
        }

    def __hash__(self) -> int:
        """Compute hash based on track ID for use in sets and dictionaries.

        Returns:
            Hash of the track's ID.
        """
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare tracks for equality based on their ID.

        Args:
            other: The object to compare against.

        Returns:
            ``True`` if *other* is a :class:`Track` with the same ID.
        """
        if not isinstance(other, Track):
            return NotImplemented
        return self.id == other.id

    def replace(self, **changes: object) -> Track:
        """Return a new :class:`Track` with the specified fields updated.

        This method follows the functional-update pattern common with frozen
        dataclasses: it does not mutate the current instance but instead
        produces a new one with the requested changes applied.

        Args:
            **changes: Field names and their new values to replace
                (e.g. ``title="New Title"``).

        Returns:
            A new :class:`Track` instance with the updated fields.
        """
        return _dc_replace(self, **changes)  # type: ignore[call-overload]
