"""Tests for the LyricsProvider."""

import tempfile
import os

from catalog.lyrics_provider import LyricsProvider
from model.track import Track


class TestLyricsProvider:
    def test_fetch_empty_path(self):
        track = Track(id=1, title="Test", artist="Artist")
        result = LyricsProvider().fetch(track)
        assert result == []

    def test_fetch_unknown_path(self):
        track = Track(id=1, title="Test", artist="Artist", lyrics_path="Unknown Lyrics Path")
        result = LyricsProvider().fetch(track)
        assert result == []

    def test_fetch_missing_file(self):
        track = Track(id=1, title="Test", artist="Artist", lyrics_path="/nonexistent/path.lrc")
        result = LyricsProvider().fetch(track)
        assert result == []

    def test_fetch_valid_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lrc", delete=False) as f:
            f.write("[00:00.00]Line 1\n[00:01.00]Line 2\n")
            f.flush()
            track = Track(id=1, title="Test", artist="Artist", lyrics_path=f.name)
            try:
                result = LyricsProvider().fetch(track)
                assert len(result) == 2
                assert result[0].text == "Line 1"
                assert result[1].text == "Line 2"
            finally:
                try:
                    os.unlink(f.name)
                except OSError:
                    pass

