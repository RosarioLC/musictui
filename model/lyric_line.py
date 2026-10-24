"""Represents a single line of synchronized lyrics."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LyricLine:
    """Immutable data class representing one line of synchronized lyrics.

    Each instance carries a precise timestamp (in milliseconds) indicating
    when the lyric line should be displayed during playback, together with
    the text content to render.  Being frozen and using slots ensures memory
    efficiency and prevents accidental mutation after construction.

    Attributes:
        timestamp_ms: Millisecond offset from the start of the track when
            this line becomes active.  Zero means "display immediately".
        text: The human-readable lyric text to present to the user.
    """

    timestamp_ms: int
    text: str
