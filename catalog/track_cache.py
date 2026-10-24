from collections import OrderedDict
from typing import Generic, TypeVar

from model.lyric_line import LyricLine
from model.track import Track

_K = TypeVar("_K")
_V = TypeVar("_V")


class _LRUCache(Generic[_K, _V]):
    """Generic LRU cache backed by an OrderedDict.

    Accessing a key moves it to the end (most-recently-used).
    When the cache exceeds *max_size*, the least-recently-used item is evicted.
    """

    def __init__(self, max_size: int = 8) -> None:
        """Initialize the cache.

        Args:
            max_size: Maximum number of items to retain.
        """
        self._max_size: int = max_size
        self._cache: OrderedDict[_K, _V] = OrderedDict()

    def get(self, key: _K) -> _V | None:
        """Retrieve a value, promoting the key to most-recently-used.

        Args:
            key: The key to look up.

        Returns:
            The value if found, else ``None``.
        """
        value = self._cache.get(key)
        if value is not None:
            self._cache.move_to_end(key)
        return value

    def put(self, key: _K, value: _V) -> None:
        """Store a key-value pair, evicting the oldest entry if full."""
        self._cache[key] = value
        self._cache.move_to_end(key)
        self._trim()

    def _trim(self) -> None:
        """Evict least-recently-used items until under *max_size*."""
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._cache.clear()


class TrackCache:
    """In-memory LRU cache for track metadata, lyrics, and stream URLs.

    Maintains three independent caches, each with its own LRU policy.
    Lyrics are keyed by a hash of (artist, title) so that different
    track objects for the same song share cached lyrics.
    """

    def __init__(self, max_size: int = 8) -> None:
        """Initialize the track cache.

        Args:
            max_size: Maximum entries per sub-cache.
        """
        self._max_size: int = max_size
        self._tracks: _LRUCache[int, Track] = _LRUCache(max_size)
        self._lyrics: _LRUCache[str, list[LyricLine]] = _LRUCache(max_size)
        self._streams: _LRUCache[int, str] = _LRUCache(max_size)

    def get(self, track_id: int) -> Track | None:
        """Retrieve a cached track by ID."""
        return self._tracks.get(track_id)

    def put(self, track: Track) -> None:
        """Cache a track by its ID."""
        self._tracks.put(track.id, track)

    @staticmethod
    def _lyrics_key(track: Track) -> str:
        """Return a cache key derived from artist + title."""
        artist = " ".join(track.artist.lower().split())
        title = " ".join(track.title.lower().split())
        return f"{artist}|{title}"

    def get_lyrics(self, track: Track) -> list[LyricLine] | None:
        """Retrieve cached lyrics for a track."""
        key = self._lyrics_key(track)
        result = self._lyrics.get(key)
        return result

    def put_lyrics(self, track: Track, lyrics: list[LyricLine]) -> None:
        """Cache lyrics for a track."""
        key = self._lyrics_key(track)
        self._lyrics.put(key, lyrics)

    @staticmethod
    def _stream_key(track: Track) -> str:
        """Return a cache key derived from the track's URL."""
        return track.url.strip()

    def get_stream(self, track: Track) -> str | None:
        """Retrieve a cached stream URL for a track."""
        return self._streams.get(self._stream_key(track))

    def put_stream(self, track: Track, stream: str) -> None:
        """Cache a stream URL for a track."""
        self._streams.put(self._stream_key(track), stream)

    def clear(self) -> None:
        """Clear all sub-caches."""
        self._tracks.clear()
        self._lyrics.clear()
        self._streams.clear()
