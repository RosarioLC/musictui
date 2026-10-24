"""Parse LRC-formatted lyrics into :class:`~model.lyric_line.LyricLine` objects."""

import re

from model.lyric_line import LyricLine

# Regex pattern for LRC timestamp lines: [mm:ss.xx] text
# Groups: 1=minutes, 2=seconds, 3=centiseconds (optional), 4=text content
_LRC_PATTERN: re.Pattern[str] = re.compile(
    r"^\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]\s*(.*)$"
)


class LyricsParser:
    """Stateless parser that converts LRC-formatted text into timestamped lyric lines.

    LRC format uses timestamps of the form ``[mm:ss.xx]`` (where ``.xx``
    is optional centiseconds) followed by lyric text.  Lines that do not
    match this pattern are silently skipped.  The output is a list of
    :class:`~model.lyric_line.LyricLine` objects ordered by their
    appearance in the source text.

    Example::

        >>> lyrics = LyricsParser.parse("[00:12.00]First line\\n[00:24.50]Second line")
        >>> len(lyrics)
        2
        >>> lyrics[0].timestamp_ms
        12000
    """

    @staticmethod
    def parse(raw_text: str) -> list[LyricLine]:
        """Convert raw LRC-formatted text into a list of timestamped lyric lines.

        Each input line is matched against the LRC timestamp pattern.
        Lines that fail to match are silently skipped.  Centiseconds
        (the optional ``.xx`` portion) are right-padded with zeros to
        form a three-digit millisecond value.

        Args:
            raw_text: The complete LRC-formatted lyrics string, which may
                contain multiple timestamped lines and non-matching content.

        Returns:
            A list of :class:`~model.lyric_line.LyricLine` objects in the
            same order as they appeared in *raw_text*.  Returns an empty
            list when no lines match the timestamp pattern.
        """
        lines: list[LyricLine] = []
        for raw_line in raw_text.splitlines():
            match = _LRC_PATTERN.match(raw_line.strip())
            if match is None:
                continue
            minutes, seconds, fraction, text = match.groups()
            milliseconds = int((fraction or "0").ljust(3, "0"))
            timestamp_ms = int(minutes) * 60_000 + int(seconds) * 1_000 + milliseconds
            lines.append(LyricLine(timestamp_ms=timestamp_ms, text=text))
        return lines
