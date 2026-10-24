"""Library service wrapping PlaylistStore."""

from __future__ import annotations

from model.playlist import Playlist
from model.track import Track
from store.playlist_store import PlaylistStore


class LibraryService:
    """Service that wraps the PlaylistStore for library operations.

    Provides playlist CRUD and liked-songs management behind
    a single interface.
    """

    LIKED_SONGS_ID: int = -1  # Reserved ID for the special "Liked Songs" playlist

    def __init__(self, store: PlaylistStore) -> None:
        self._store = store

    @property
    def store(self) -> PlaylistStore:
        return self._store

    def create_playlist(self, name: str) -> Playlist:
        return self._store.create(name)

    def delete_playlist(self, playlist_id: int) -> None:
        self._store.delete(playlist_id)

    def rename_playlist(self, playlist_id: int, new_name: str) -> None:
        self._store.rename(playlist_id, new_name)

    def list_playlists(self) -> list[Playlist]:
        return self._store.list()

    def get_liked_songs(self) -> list[Track]:
        return self._store.get_liked_songs()

    def is_liked(self, track: Track) -> bool:
        return self._store.is_liked(track)

    def add_to_liked_songs(self, track: Track) -> None:
        self._store.add_to_liked_songs(track)

    def remove_from_liked_songs(self, track: Track) -> None:
        self._store.remove_from_liked_songs(track)

    def add_song(self, playlist_id: int, track: Track) -> None:
        self._store.add_song(playlist_id, track)

    def remove_song(self, playlist_id: int, track: Track) -> None:
        self._store.remove_song(playlist_id, track)
