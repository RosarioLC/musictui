import random
from collections.abc import Iterator

from model.repeat_mode import RepeatMode
from model.track import Track


class MusicQueue:
    """Manages the playback queue with repeat and history support.

    The queue maintains three internal structures:

    * ``_tracks`` — the upcoming tracks to play.
    * ``_track_ids`` — a set of track IDs for O(1) lookups.
    * ``_history`` — tracks that have already been played (for "back" navigation).
    * ``_current`` — the currently playing track.

    Repeat modes cycle through OFF → ALL → ONE.
    """

    def __init__(
        self,
        tracks: list[Track] | None = None,
        repeat: RepeatMode = RepeatMode.OFF,
    ) -> None:
        """Initialize the queue.

        Args:
            tracks: Initial tracks to add.  May be ``None``.
            repeat: Starting repeat mode.
        """
        self._repeat: RepeatMode = repeat
        self._history: list[Track] = []
        self._current: Track | None = None
        self._tracks: list[Track] = list(tracks) if tracks else []
        # Set of track IDs for O(1) membership testing.
        self._track_ids: set[int] = {t.id for t in self._tracks}

    def play_next(self) -> Track | None:
        """Advance to the next track in the queue.

        If the queue is empty and repeat mode is ALL with history available,
        the history is restored to the queue for a full repeat.

        Returns:
            The newly current track, or ``None`` if there are no more tracks.
        """
        if not self._tracks:
            if self._repeat == RepeatMode.ALL and self._history:
                self._tracks = self._history
                self._track_ids = {t.id for t in self._tracks}
                self._history = []
            else:
                return None
        if self._current is not None:
            self._history.append(self._current)
        self._current = self._tracks.pop(0)
        self._track_ids.discard(self._current.id)
        return self._current

    def play_previous(self) -> Track | None:
        """Revert to the previously played track.

        Returns:
            The previous track, or ``None`` if no history exists.
        """
        if not self._history:
            return None
        if self._current is not None:
            self._tracks.insert(0, self._current)
            self._track_ids.add(self._current.id)
        self._current = self._history.pop()
        self._track_ids.discard(self._current.id)
        return self._current

    def skip_to(self, track: Track) -> None:
        """Set *track* as the current track, removing it from the upcoming queue.

        Args:
            track: The track to skip to.

        Raises:
            ValueError: If *track* is not in the queue and is not the current track.
        """
        if self._current == track:
            return
        if track.id not in self._track_ids:
            raise ValueError("Track is not in the queue")
        if self._current is not None:
            self._history.append(self._current)
        self._tracks.remove(track)
        self._track_ids.discard(track.id)
        self._current = track

    def shuffle(self) -> None:
        """Randomize the order of upcoming tracks in-place."""
        random.shuffle(self._tracks)

    def toggle_repeat(self) -> None:
        """Cycle the repeat mode: OFF → ALL → ONE → OFF."""
        self._repeat = self._repeat.next_mode()

    def add(self, track: Track) -> None:
        """Add *track* to the end of the queue if not already present.

        Args:
            track: The track to add.
        """
        current = self._current
        if (
            current is None or track.id != current.id
        ) and track.id not in self._track_ids:
            self._tracks.append(track)
            self._track_ids.add(track.id)

    def replace_upcoming(self, tracks: list[Track]) -> None:
        """Replace all upcoming tracks, excluding the current one."""
        self._tracks = [t for t in tracks if t != self._current]
        self._track_ids = {t.id for t in self._tracks}

    def contains(self, track: Track) -> bool:
        """Check whether *track* is the current or an upcoming track."""
        current = self._current
        return (
            current is not None and track.id == current.id
        ) or track.id in self._track_ids

    @property
    def current(self) -> Track | None:
        """The currently playing track, or ``None``."""
        return self._current

    @property
    def is_empty(self) -> bool:
        """``True`` if there are no tracks in the queue or history."""
        return not self._tracks and not self._history and self._current is None

    @property
    def upcoming(self) -> list[Track]:
        """A snapshot of the upcoming tracks (does not include current)."""
        return list(self._tracks)

    @property
    def repeat(self) -> RepeatMode:
        """The current repeat mode."""
        return self._repeat

    def __iter__(self) -> Iterator[Track]:
        """Iterate over upcoming tracks."""
        return iter(self._tracks)
