"""Tests for the LRC lyrics parser with edge cases."""

from catalog.lyrics_parser import LyricsParser
from model.lyric_line import LyricLine


class TestLyricsParser:
    """Extended tests for LRC parsing."""

    def test_parse_empty(self):
        assert LyricsParser.parse("") == []

    def test_parse_simple(self):
        text = "[00:00.00]First line\n[00:01.00]Second line"
        result = LyricsParser.parse(text)
        assert len(result) == 2
        assert isinstance(result[0], LyricLine)

    def test_parse_centiseconds(self):
        """Centiseconds are right-padded to milliseconds."""
        result = LyricsParser.parse("[00:12.5]Line")
        assert len(result) == 1
        assert result[0].timestamp_ms == 12500

    def test_parse_centiseconds_three_digits(self):
        """Three-digit centiseconds are used as-is."""
        result = LyricsParser.parse("[00:12.345]Line")
        assert len(result) == 1
        assert result[0].timestamp_ms == 12345

    def test_skip_non_matching_lines(self):
        """Lines without timestamps are silently skipped."""
        text = "Intro\n[00:05.00]First line\nBridge\n[00:10.00]Second line"
        result = LyricsParser.parse(text)
        assert len(result) == 2

    def test_parse_large_timestamp(self):
        """Timestamps beyond a single minute work correctly."""
        result = LyricsParser.parse("[10:30.00]Late line")
        assert len(result) == 1
        assert result[0].timestamp_ms == 630000

    def test_parse_empty_text(self):
        """Lines with timestamp but empty text are included."""
        result = LyricsParser.parse("[00:00.00]  ")
        assert len(result) == 1
        assert result[0].text == ""

    def test_parse_many_lines(self):
        """Parsing many lines produces correct count."""
        # Use valid timestamps: 00:00 to 59:59 range
        lines = []
        for i in range(100):
            minutes = i // 60
            seconds = i % 60
            lines.append(f"[{minutes:02d}:{seconds:02d}.00]Line {i}")
        result = LyricsParser.parse("\n".join(lines))
        assert len(result) == 100
        assert result[0].timestamp_ms == 0
        # Line 99: minutes=1, seconds=39 => 60000 + 39000 = 99000
        assert result[99].timestamp_ms == 99000

    def test_parse_whitespace_only(self):
        assert LyricsParser.parse("   \n  \n  ") == []

    def test_parse_mixed_valid_invalid(self):
        text = "garbage\n[00:00.00]valid\nmore garbage\n[01:00.00]also valid"
        result = LyricsParser.parse(text)
        assert len(result) == 2
        assert result[0].timestamp_ms == 0
        assert result[1].timestamp_ms == 60000

    def test_parse_single_digit_minute(self):
        """Single-digit minutes are handled."""
        result = LyricsParser.parse("[5:30.00]Line")
        assert len(result) == 1
        assert result[0].timestamp_ms == 330000

    def test_parse_no_centiseconds(self):
        """Timestamps without centiseconds work."""
        result = LyricsParser.parse("[00:30]Line")
        assert len(result) == 1
        assert result[0].timestamp_ms == 30000

    def test_lyric_line_attributes(self):
        """Each LyricLine has correct timestamp and text."""
        result = LyricsParser.parse("[02:15.500]Hello world")
        assert result[0].timestamp_ms == 135500
        assert result[0].text == "Hello world"

    def test_parse_duplicate_timestamps(self):
        """Duplicate timestamps are preserved as separate lines."""
        result = LyricsParser.parse("[00:00.00]First\n[00:00.00]Second")
        assert len(result) == 2
        assert result[0].text == "First"
        assert result[1].text == "Second"

