"""Tests for the Track model with comprehensive edge cases."""

import zlib
from model.track import Track


class TestTrack:
    """Comprehensive tests for the Track frozen dataclass."""

    def test_create(self):
        t = Track(id=1, title="Test", artist="Artist")
        assert t.id == 1
        assert t.title == "Test"
        assert t.artist == "Artist"

    def test_defaults(self):
        t = Track(id=1)
        assert t.title == "Unknown Title"
        assert t.artist == "Unknown Artist"
        assert t.album == "Unknown Album"
        assert t.duration_ms == 0
        assert t.image_path == "Unknown Image Path"
        assert t.lyrics_path == "Unknown Lyrics Path"
        assert t.url == ""
        assert t.provider_id == ""

    def test_to_dict(self):
        t = Track(
            id=1, title="Test", artist="Artist", album="Album",
            duration_ms=180000, provider_id="vid123",
        )
        d = t.to_dict()
        assert d["id"] == 1
        assert d["title"] == "Test"
        assert d["artist"] == "Artist"
        assert d["album"] == "Album"
        assert d["duration_ms"] == 180000
        assert d["provider_id"] == "vid123"
        assert "url" in d

    def test_replace(self):
        t = Track(id=1, title="Old", artist="Old")
        new_t = t.replace(title="New", artist="New")
        assert new_t.id == 1
        assert new_t.title == "New"
        assert new_t.artist == "New"
        assert t.title == "Old"
        assert t.artist == "Old"

    def test_replace_id_unchanged(self):
        t = Track(id=42, title="Test")
        new_t = t.replace(title="Changed")
        assert new_t.id == 42

    def test_replace_duration(self):
        t = Track(id=1, duration_ms=100)
        new_t = t.replace(duration_ms=200)
        assert new_t.duration_ms == 200
        assert t.duration_ms == 100

    def test_immutability(self):
        t = Track(id=1, title="Test")
        try:
            t.title = "Changed"
            assert False, "Should not mutate frozen dataclass"
        except Exception:
            pass

    def test_hash_and_equality(self):
        t1 = Track(id=1, title="Test")
        t2 = Track(id=1, title="Different")
        t3 = Track(id=2, title="Test")
        assert t1 == t2
        assert t1 != t3
        assert hash(t1) == hash(t2)
        assert hash(t1) != hash(t3)

    def test_hash_in_set(self):
        t1 = Track(id=1, title="Test")
        t2 = Track(id=1, title="Different")
        s = {t1}
        assert t2 in s

    def test_hash_in_dict(self):
        t1 = Track(id=1, title="Test")
        t2 = Track(id=1, title="Different")
        d = {t1: "value"}
        assert d[t2] == "value"

    def test_normalize_empty_title(self):
        t = Track(id=1, title="  ")
        assert t.title == "Unknown Title"

    def test_normalize_empty_artist(self):
        t = Track(id=1, artist="  ")
        assert t.artist == "Unknown Artist"

    def test_normalize_empty_album(self):
        t = Track(id=1, album="  ")
        assert t.album == "Unknown Album"

    def test_normalize_empty_image_path(self):
        t = Track(id=1, image_path="  ")
        assert t.image_path == "Unknown Image Path"

    def test_normalize_empty_lyrics_path(self):
        t = Track(id=1, lyrics_path="  ")
        assert t.lyrics_path == "Unknown Lyrics Path"

    def test_normalize_empty_url(self):
        t = Track(id=1, url="  ")
        assert t.url == ""

    def test_clamp_negative_duration(self):
        t = Track(id=1, duration_ms=-100)
        assert t.duration_ms == 0

    def test_crc32_id_generation(self):
        vid = "dQw4w9WgXcQ"
        expected_id = zlib.crc32(vid.encode("utf-8")) & 0xFFFFFFFF
        t = Track(id=expected_id, provider_id=vid)
        assert t.id == expected_id
        assert t.provider_id == vid

    def test_equality_with_non_track(self):
        t = Track(id=1, title="Test")
        assert t != "not a track"
        assert t != 1
        assert t != None

    def test_hash_consistency(self):
        t = Track(id=1, title="Test")
        h1 = hash(t)
        h2 = hash(t)
        assert h1 == h2

    def test_replace_preserves_unspecified_fields(self):
        t = Track(id=1, title="T", artist="A", album="Al", duration_ms=100)
        new_t = t.replace(title="New")
        assert new_t.artist == "A"
        assert new_t.album == "Al"
        assert new_t.duration_ms == 100

