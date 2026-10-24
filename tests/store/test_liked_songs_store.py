"""Tests for the LikedSongStore with full CRUD."""

import pytest

from model.track import Track
from store.database import Database
from store.liked_song_store import LikedSongStore


class TestLikedSongStore:
    @pytest.fixture
    def db(self):
        return Database(":memory:")

    def test_add(self, db):
        t = Track(id=1, title="Test", provider_id="test_video_id")
        store = LikedSongStore(db)
        store.add(t)
        db.commit()
        ids = store.list_ids()
        assert "test_video_id" in ids

    def test_add_duplicate_ignored(self, db):
        t = Track(id=1, title="Test", provider_id="vid1")
        store = LikedSongStore(db)
        store.add(t)
        store.add(t)
        db.commit()
        ids = store.list_ids()
        assert ids.count("vid1") == 1

    def test_remove(self, db):
        t = Track(id=1, title="Test", provider_id="vid1")
        store = LikedSongStore(db)
        store.add(t)
        store.remove(t)
        db.commit()
        assert store.list_ids() == []

    def test_remove_not_present(self, db):
        t = Track(id=1, title="Test", provider_id="vid1")
        store = LikedSongStore(db)
        store.remove(t)
        db.commit()
        assert store.list_ids() == []

    def test_list_ids_empty(self, db):
        store = LikedSongStore(db)
        assert store.list_ids() == []

    def test_list_ids_multiple(self, db):
        store = LikedSongStore(db)
        store.add(Track(id=1, provider_id="vid1"))
        store.add(Track(id=2, provider_id="vid2"))
        store.add(Track(id=3, provider_id="vid3"))
        db.commit()
        ids = store.list_ids()
        assert len(ids) == 3

    def test_list_ids_order(self, db):
        store = LikedSongStore(db)
        store.add(Track(id=1, provider_id="charlie"))
        store.add(Track(id=2, provider_id="alpha"))
        store.add(Track(id=3, provider_id="bravo"))
        db.commit()
        ids = store.list_ids()
        assert ids == ["alpha", "bravo", "charlie"]

