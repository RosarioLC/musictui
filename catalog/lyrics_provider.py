from catalog.lyrics_parser import LyricsParser
from model.lyric_line import LyricLine
from model.track import Track


class LyricsProvider:
    """Fetches lyrics for a track from a local file."""

    def fetch(self, track: Track) -> list[LyricLine]:
        """Read and parse lyrics from the track's lyrics file.

        If the track has no lyrics path, or the file cannot be read,
        an empty list is returned.

        Args:
            track: The track whose lyrics to fetch.

        Returns:
            A list of :class:`~model.lyric_line.LyricLine` objects,
            or an empty list on failure.
        """
        if not track.lyrics_path or track.lyrics_path.startswith("Unknown"):
            return []
        try:
            with open(track.lyrics_path, encoding="utf-8") as lyrics_file:
                return LyricsParser.parse(lyrics_file.read())
        except OSError:
            return []
