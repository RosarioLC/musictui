"""Tests for the Playlist model with comprehensive edge cases."""

from model.playlist import Playlist
from model.track import Track


class TestPlaylist:
    """Comprehensive tests for the Playlist model."""

    def test_create(self):
        p = Playlist(id=1, name="Test", songs=[])
        assert p.id == 1
        assert p.name == "Test"
        assert p.songs == []

    def test_create_none_songs(self):
        p = Playlist(id=1, name="Test", songs=None)
        assert p.songs == []

    def test_create_default_name(self):
        p = Playlist(id=1, name=None, songs=[])
        assert p.name == "No Name"

    def test_create_whitespace_name(self):
        p = Playlist(id=1, name="   ", songs=[])
        assert p.name == "No Name"

    def test_add_song(self):
        p = Playlist(id=1, name="Test", songs=[])
        t = Track(id=1, title="Test")
        p.add_song(t)
        assert len(p.songs) == 1

    def test_add_song_position_advances(self):
        p = Playlist(id=1, name="Test", songs=[])
        t = Track(id=1, title="Test")
        p.add_song(t)
        assert p.position == 1

    def test_add_duplicate_song_raises(self):
        t = Track(id=1, title="Test")
        p = Playlist(id=1, name="Test", songs=[t])
        try:
            p.add_song(t)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_add_none_raises(self):
        p = Playlist(id=1, name="Test", songs=[])
        try:
            p.add_song(None)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_remove_song(self):
        t = Track(id=1, title="Test")
        p = Playlist(id=1, name="Test", songs=[t])
        p.remove_song(t)
        assert len(p.songs) == 0

    def test_remove_song_position_resets(self):
        t = Track(id=1, title="Test")
        p = Playlist(id=1, name="Test", songs=[t])
        p.remove_song(t)
        assert p.position == 0

    def test_remove_not_in_playlist_raises(self):
        t = Track(id=99, title="Not in playlist")
        p = Playlist(id=1, name="Test", songs=[])
        try:
            p.remove_song(t)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_remove_none_raises(self):
        p = Playlist(id=1, name="Test", songs=[])
        try:
            p.remove_song(None)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_contains_with_track(self):
        t = Track(id=1, title="Test")
        p = Playlist(id=1, name="Test", songs=[t])
        assert t in p

    def test_contains_false_for_missing(self):
        p = Playlist(id=1, name="Test", songs=[])
        assert Track(id=99, title="Missing") not in p

    def test_contains_non_track(self):
        p = Playlist(id=1, name="Test", songs=[])
        assert "not a track" not in p
        assert 42 not in p

    def test_contains_uses_id(self):
        t1 = Track(id=1, title="Test")
        t2 = Track(id=1, title="Different")
        p = Playlist(id=1, name="Test", songs=[t1])
        assert t2 in p

    def test_next_song(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        t3 = Track(id=3, title="3")
        p = Playlist(id=1, name="Test", songs=[t1, t2, t3])
        assert p.next_song(t1) == t2
        assert p.next_song(t2) == t3

    def test_next_song_last_raises(self):
        p = Playlist(id=1, name="Test", songs=[Track(id=1)])
        try:
            p.next_song(p.songs[0])
            assert False, "Should raise IndexError"
        except IndexError:
            pass

    def test_previous_song(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        t3 = Track(id=3, title="3")
        p = Playlist(id=1, name="Test", songs=[t1, t2, t3])
        assert p.previous_song(t3) == t2
        assert p.previous_song(t2) == t1

    def test_previous_song_first_raises(self):
        p = Playlist(id=1, name="Test", songs=[Track(id=1)])
        try:
            p.previous_song(p.songs[0])
            assert False, "Should raise IndexError"
        except IndexError:
            pass

    def test_iteration(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        p = Playlist(id=1, name="Test", songs=[t1, t2])
        songs = list(p)
        assert songs == [t1, t2]

    def test_len(self):
        p = Playlist(id=1, name="Test", songs=[])
        assert len(p) == 0
        p.add_song(Track(id=1))
        p.add_song(Track(id=2))
        assert len(p) == 2

    def test_name_setter(self):
        p = Playlist(id=1, name="Old", songs=[])
        p.name = "New"
        assert p.name == "New"

    def test_name_setter_strips_whitespace(self):
        p = Playlist(id=1, name="Old", songs=[])
        p.name = "  New  "
        assert p.name == "New"

    def test_name_setter_none_ignored(self):
        p = Playlist(id=1, name="Old", songs=[])
        p.name = None
        assert p.name == "Old"

    def test_o1_membership(self):
        """Membership test is O(1) via set lookup."""
        songs = [Track(id=i, title=f"Song {i}") for i in range(1000)]
        p = Playlist(id=1, name="Test", songs=songs)
        assert Track(id=999, title="Song 999") in p
        assert Track(id=9999, title="Missing") not in p

    def test_remove_preserves_remaining_order(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        t3 = Track(id=3, title="3")
        p = Playlist(id=1, name="Test", songs=[t1, t2, t3])
        p.remove_song(t2)
        assert p.songs == [t1, t3]

    def test_add_song_not_in_playlist_raises(self):
        p = Playlist(id=1, name="Test", songs=[])
        try:
            p.add_song(None)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

