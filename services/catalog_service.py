"""Catalog service wrapping YTMusicSource + TrackCache."""

from __future__ import annotations

from catalog.catalog_source import CatalogSource
from catalog.track_cache import TrackCache
from model.lyric_line import LyricLine
from model.track import Track


class CatalogService:
    """Service that wraps the catalog source and cache.

    Provides search, recommendations, lyrics, and caching
    behind a single interface.
    """

    def __init__(
        self,
        source: CatalogSource,
        cache: TrackCache,
    ) -> None:
        self._source = source
        self._cache = cache

    def search(self, query: str) -> list[Track]:
        return self._source.search(query)

    def get_track(self, track_id: int) -> Track | None:
        cached = self._cache.get(track_id)
        if cached is not None:
            return cached
        return self._source.get_track(track_id)

    def get_recommended_tracks(self, limit: int = 12) -> list[Track]:
        return self._source.get_recommended_tracks(limit)

    def get_lyrics(self, track: Track) -> list[LyricLine]:
        """Fetch lyrics for *track*, using the cache when available."""
        cached = self._cache.get_lyrics(track)
        if cached is not None:
            return cached
        lyrics = self._source.get_lyrics(track)
        if lyrics:
            self._cache.put_lyrics(track, lyrics)
        return lyrics

    def get_stream(self, track: Track) -> str:
        """Resolve a playable stream URL for *track* via the source."""
        cached = self._cache.get_stream(track)
        if cached is not None:
            return cached
        stream = self._source.get_track_stream_url(track)
        if stream:
            self._cache.put_stream(track, stream)
        return stream
