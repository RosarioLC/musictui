"""Enum defining the available repeat modes for playback."""

from enum import Enum


class RepeatMode(Enum):
    """Enumeration of the three repeat modes supported by the playback queue.

    The modes form a cycle: ``OFF`` (no repeat) -> ``ALL`` (repeat entire
    queue) -> ``ONE`` (repeat current track) -> ``OFF``.  Each mode is
    represented by an integer value that determines its position in the
    cycle.

    Attributes:
        OFF: Play each track once and stop when the queue is exhausted.
        ALL: When the queue ends, rewind to the beginning and replay all
            tracks from history.
        ONE: Immediately restart the current track when it finishes.
    """

    OFF = 0
    ALL = 1
    ONE = 2

    def next_mode(self) -> "RepeatMode":
        """Return the next mode in the repeat cycle.

        The cycle proceeds as OFF (0) -> ALL (1) -> ONE (2) -> OFF (0).

        Returns:
            The next :class:`RepeatMode` in the sequence.
        """
        return RepeatMode((self.value + 1) % 3)
