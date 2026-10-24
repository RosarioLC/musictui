"""Tests for the PlaylistStore with full CRUD and track resolution."""

import pytest

from model.track import Track
from store.database import Database
from store.playlist_store import PlaylistStore


class TestPlaylistStore:
    @pytest.fixture
    def db(self):
        return Database(":memory:")

    def test_create(self, db):
        store = PlaylistStore(db)
        p = store.create("Test")
        assert p.name == "Test"

    def test_create_default_name(self, db):
        store = PlaylistStore(db)
        p = store.create("")
        assert p.name == "No Name"

    def test_create_whitespace_name(self, db):
        store = PlaylistStore(db)
        p = store.create("   ")
        assert p.name == "No Name"

    def test_list(self, db):
        store = PlaylistStore(db)
        store.create("A")
        store.create("B")
        playlists = store.list()
        assert len(playlists) >= 3  # includes Liked Songs

    def test_delete(self, db):
        store = PlaylistStore(db)
        p = store.create("To Delete")
        store.delete(p.id)
        playlists = store.list()
        assert all(pl.name != "To Delete" for pl in playlists)

    def test_rename(self, db):
        store = PlaylistStore(db)
        p = store.create("Old Name")
        store.rename(p.id, "New Name")
        playlists = store.list()
        found = next(pl for pl in playlists if pl.id == p.id)
        assert found.name == "New Name"

    def test_add_song(self, db):
        store = PlaylistStore(db)
        p = store.create("Test")
        t = Track(id=1, title="Test", provider_id="vid1")
        store.add_song(p.id, t)
        playlists = store.list()
        playlist = next(pl for pl in playlists if pl.id == p.id)
        assert len(playlist.songs) == 1
        assert playlist.songs[0].title == "Test"

    def test_add_song_resolves_by_provider_id(self, db):
        """Track with zlib.crc32 id should resolve via provider_id."""
        store = PlaylistStore(db)
        p = store.create("Test")
        t = Track(id=999999, title="Test", provider_id="my_video_id")
        store.add_song(p.id, t)
        playlists = store.list()
        playlist = next(pl for pl in playlists if pl.id == p.id)
        assert len(playlist.songs) == 1

    def test_add_duplicate_song_raises(self, db):
        store = PlaylistStore(db)
        p = store.create("Test")
        t = Track(id=1, title="Test", provider_id="vid1")
        store.add_song(p.id, t)
        try:
            store.add_song(p.id, t)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_remove_song(self, db):
        store = PlaylistStore(db)
        p = store.create("Test")
        t = Track(id=1, title="Test", provider_id="vid1")
        store.add_song(p.id, t)
        store.remove_song(p.id, t)
        playlists = store.list()
        playlist = next(pl for pl in playlists if pl.id == p.id)
        assert len(playlist.songs) == 0

    def test_get_liked_songs(self, db):
        store = PlaylistStore(db)
        t1 = Track(id=1, title="Song1", provider_id="vid1")
        t2 = Track(id=2, title="Song2", provider_id="vid2")
        store.add_to_liked_songs(t1)
        store.add_to_liked_songs(t2)
        liked = store.get_liked_songs()
        assert len(liked) == 2

    def test_is_liked(self, db):
        store = PlaylistStore(db)
        t = Track(id=1, title="Test", provider_id="vid1")
        assert store.is_liked(t) is False
        store.add_to_liked_songs(t)
        assert store.is_liked(t) is True

    def test_remove_from_liked_songs(self, db):
        store = PlaylistStore(db)
        t = Track(id=1, title="Test", provider_id="vid1")
        store.add_to_liked_songs(t)
        store.remove_from_liked_songs(t)
        assert store.is_liked(t) is False

    def test_liked_songs_playlist_exists(self, db):
        store = PlaylistStore(db)
        playlists = store.list()
        liked = next((p for p in playlists if p.id == -1), None)
        assert liked is not None
        assert liked.name == "Liked Songs"

