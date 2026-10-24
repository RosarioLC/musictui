"""Playlist model containing a sequence of tracks."""

from collections.abc import Iterator

from model.track import Track


class Playlist:
    """Ordered collection of tracks with O(1) membership testing and navigation.

    Internally maintains both a list (for ordered iteration and index-based
    access) and a set of track IDs (for fast membership checks), keeping them
    in sync during all mutations.  The cursor position tracks the currently
    selected track within the playlist.

    This class supports iteration, length queries, membership testing, and
    navigation helpers (:meth:`next_song`, :meth:`previous_song`).

    Attributes:
        _id: Unique integer identifier for the playlist.
        _name: Display name, defaulting to ``"No Name"`` if falsy.
        _songs: Ordered list of :class:`Track` objects.
        _position: Zero-based cursor position within the playlist.
        _song_ids: Set of track IDs for O(1) membership testing.
    """

    def __init__(
        self, id: int, name: str | None, songs: list[Track] | None, position: int = 0
    ) -> None:
        """Initialize a new playlist with optional initial tracks.

        Args:
            id: Unique integer identifier for the playlist.
            name: Display name. Defaults to ``"No Name"`` if falsy or
                whitespace-only.
            songs: Initial track list. Defaults to an empty list if ``None``.
            position: Initial cursor position. Defaults to zero.
        """
        self._id: int = id
        self._name: str = name.strip() if name and name.strip() else "No Name"
        self._songs: list[Track] = list(songs) if songs else []
        self._position: int = position
        self._song_ids: set[int] = {t.id for t in self._songs}

    @property
    def id(self) -> int:
        """Return the unique integer identifier for this playlist."""
        return self._id

    @property
    def name(self) -> str:
        """Return the display name of the playlist."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        """Update the playlist name, stripping surrounding whitespace.

        Args:
            value: The new name. If falsy or whitespace-only, the name
                is not changed.
        """
        if value and value.strip():
            self._name = value.strip()

    @property
    def songs(self) -> list[Track]:
        """Return the ordered list of tracks in this playlist."""
        return self._songs

    @property
    def position(self) -> int:
        """Return the current cursor position within the playlist."""
        return self._position

    def __iter__(self) -> Iterator[Track]:
        """Return an iterator over the tracks in order."""
        return iter(self._songs)

    def __len__(self) -> int:
        """Return the number of tracks in the playlist."""
        return len(self._songs)

    def __contains__(self, track: object) -> bool:
        """Check whether a track is present using O(1) set lookup.

        Args:
            track: The track to check, or any other object.

        Returns:
            ``True`` if the track is in the playlist, ``False`` otherwise.
        """
        if isinstance(track, Track):
            return track.id in self._song_ids
        return track in self._songs

    def add_song(self, track: Track) -> None:
        """Append a track to the end of the playlist.

        Args:
            track: The track to add.

        Raises:
            ValueError: If *track* is ``None`` or already present in the
                playlist.
        """
        if track is None:
            raise ValueError("Track is null")
        if track.id in self._song_ids:
            raise ValueError("Track is already in the collection")
        self._songs.append(track)
        self._song_ids.add(track.id)
        self._position += 1

    def remove_song(self, track: Track) -> None:
        """Remove a track from the playlist.

        Args:
            track: The track to remove.

        Raises:
            ValueError: If *track* is ``None`` or not present.
        """
        if track is None:
            raise ValueError("Track is null")
        if track.id not in self._song_ids:
            raise ValueError("Track is not in the playlist")
        self._songs.remove(track)
        self._song_ids.discard(track.id)
        if not self._songs:
            self._position = 0

    def next_song(self, track: Track) -> Track:
        """Return the track that follows *track* in the playlist.

        Args:
            track: The current track.

        Returns:
            The next :class:`Track` in the sequence.

        Raises:
            IndexError: If *track* is the last track in the playlist.
        """
        index = self._index_of(track)
        if index + 1 >= len(self._songs):
            raise IndexError("No next song")
        return self._songs[index + 1]

    def previous_song(self, track: Track) -> Track:
        """Return the track that precedes *track* in the playlist.

        Args:
            track: The current track.

        Returns:
            The previous :class:`Track` in the sequence.

        Raises:
            IndexError: If *track* is the first track in the playlist.
        """
        index = self._index_of(track)
        if index <= 0:
            raise IndexError("No previous song")
        return self._songs[index - 1]

    def _index_of(self, track: Track) -> int:
        """Return the zero-based index of *track* within the playlist.

        Args:
            track: The track to locate.

        Returns:
            The zero-based index of the track in the internal list.

        Raises:
            ValueError: If *track* is ``None`` or not present in the playlist.
        """
        if track is None or track not in self._songs:
            raise ValueError("Track is not in the playlist")
        return self._songs.index(track)
