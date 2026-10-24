"""Tests for the generic LRU cache and TrackCache."""

from catalog.track_cache import _LRUCache, TrackCache
from model.lyric_line import LyricLine
from model.track import Track


class TestLRUCache:
    """Tests for the generic _LRUCache implementation."""

    def test_put_and_get(self):
        cache = _LRUCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.get("a") == 1
        assert cache.get("b") == 2

    def test_get_missing_key(self):
        cache = _LRUCache(max_size=3)
        assert cache.get("missing") is None

    def test_eviction_when_full(self):
        cache = _LRUCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # evicts "a"
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_lru_promotion(self):
        """Accessing a key moves it to most-recently-used position."""
        cache = _LRUCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.get("a")  # promotes "a" to MRU
        cache.put("d", 4)  # evicts "b" (was LRU)
        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_put_updates_existing_key(self):
        cache = _LRUCache(max_size=3)
        cache.put("a", 1)
        cache.put("a", 2)
        assert cache.get("a") == 2
        assert len(cache._cache) == 1

    def test_clear(self):
        cache = _LRUCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert len(cache._cache) == 0

    def test_max_size_one(self):
        cache = _LRUCache(max_size=1)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.get("a") is None
        assert cache.get("b") == 2


class TestTrackCache:
    """Tests for the TrackCache (tracks, lyrics, streams sub-caches)."""

    def test_put_and_get_track(self):
        cache = TrackCache(max_size=5)
        t = Track(id=1, title="Test", artist="Artist")
        cache.put(t)
        assert cache.get(1) is not None
        assert cache.get(1).title == "Test"

    def test_get_missing_track(self):
        cache = TrackCache(max_size=5)
        assert cache.get(999) is None

    def test_track_cache_eviction(self):
        cache = TrackCache(max_size=2)
        cache.put(Track(id=1, title="1"))
        cache.put(Track(id=2, title="2"))
        cache.put(Track(id=3, title="3"))  # evicts id=1
        assert cache.get(1) is None
        assert cache.get(2) is not None
        assert cache.get(3) is not None

    def test_lyrics_key_normalization(self):
        """Lyrics key normalizes whitespace and lowercases."""
        cache = TrackCache()
        t1 = Track(id=1, title="  Hello World  ", artist="  The Band  ")
        t2 = Track(id=2, title="Hello World", artist="The Band")
        assert cache._lyrics_key(t1) == cache._lyrics_key(t2)

    def test_put_and_get_lyrics(self):
        cache = TrackCache(max_size=5)
        t = Track(id=1, title="Test", artist="Artist")
        lyrics = [LyricLine(timestamp_ms=0, text="Line 1")]
        cache.put_lyrics(t, lyrics)
        result = cache.get_lyrics(t)
        assert result is not None
        assert len(result) == 1
        assert result[0].text == "Line 1"

    def test_lyrics_cache_hit_different_track_object(self):
        """Lyrics are shared across different Track objects for same song."""
        cache = TrackCache(max_size=5)
        t1 = Track(id=1, title="Test", artist="Artist")
        t2 = Track(id=99, title="Test", artist="Artist")
        cache.put_lyrics(t1, [LyricLine(timestamp_ms=0, text="Hello")])
        assert cache.get_lyrics(t2) is not None

    def test_get_lyrics_missing(self):
        cache = TrackCache(max_size=5)
        t = Track(id=1, title="Test", artist="Artist")
        assert cache.get_lyrics(t) is None

    def test_put_and_get_stream(self):
        cache = TrackCache(max_size=5)
        t = Track(id=1, title="Test", artist="Artist", url="https://example.com/1")
        cache.put_stream(t, "https://stream.example.com/audio.mp3")
        result = cache.get_stream(t)
        assert result == "https://stream.example.com/audio.mp3"

    def test_stream_key_normalization(self):
        """Stream key strips whitespace from URL."""
        cache = TrackCache()
        t1 = Track(id=1, url="  https://example.com  ")
        t2 = Track(id=2, url="https://example.com")
        assert cache._stream_key(t1) == cache._stream_key(t2)

    def test_stream_cache_miss(self):
        cache = TrackCache(max_size=5)
        t = Track(id=1, url="https://example.com")
        assert cache.get_stream(t) is None

    def test_clear_all_caches(self):
        cache = TrackCache(max_size=5)
        t = Track(id=1, title="Test", url="https://example.com")
        cache.put(t)
        cache.put_lyrics(t, [LyricLine(timestamp_ms=0, text="Lyric")])
        cache.put_stream(t, "https://stream.example.com")
        cache.clear()
        assert cache.get(1) is None
        assert cache.get_lyrics(t) is None
        assert cache.get_stream(t) is None

    def test_lyrics_key_space_normalization(self):
        """Multiple spaces and different casing produce same key."""
        cache = TrackCache()
        t1 = Track(id=1, title="  Hello   World  ", artist="  The  Band  ")
        t2 = Track(id=2, title="HELLO WORLD", artist="THE BAND")
        assert cache._lyrics_key(t1) == cache._lyrics_key(t2)
