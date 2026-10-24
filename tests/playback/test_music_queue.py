"""Tests for the MusicQueue with repeat, history, and shuffle."""

import random

from model.repeat_mode import RepeatMode
from model.track import Track
from playback.music_queue import MusicQueue


class TestMusicQueue:
    def test_create(self):
        q = MusicQueue()
        assert q.current is None
        assert q.is_empty is True

    def test_create_with_tracks(self):
        t1 = Track(id=1, title="1")
        q = MusicQueue(tracks=[t1])
        assert q.is_empty is False
        assert len(q.upcoming) == 1

    def test_skip_to(self):
        t = Track(id=1, title="Test")
        q = MusicQueue(tracks=[t])
        q.skip_to(t)
        assert q.current == t

    def test_skip_to_not_in_queue_raises(self):
        t = Track(id=99, title="Missing")
        q = MusicQueue(tracks=[Track(id=1)])
        try:
            q.skip_to(t)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_play_next(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        q = MusicQueue(tracks=[t1, t2])
        result = q.play_next()
        assert result == t1

    def test_play_next_empty(self):
        q = MusicQueue()
        assert q.play_next() is None

    def test_play_next_moves_through_queue(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        t3 = Track(id=3, title="3")
        q = MusicQueue(tracks=[t1, t2, t3])
        assert q.play_next() == t1
        assert q.play_next() == t2
        assert q.play_next() == t3
        assert q.play_next() is None

    def test_play_previous(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        q = MusicQueue(tracks=[t1, t2])
        q.play_next()  # t1 is current
        q.play_next()  # t2 is current, t1 in history
        result = q.play_previous()
        assert result == t1

    def test_play_previous_no_history(self):
        q = MusicQueue()
        assert q.play_previous() is None

    def test_add_track(self):
        q = MusicQueue()
        t = Track(id=1, title="1")
        q.add(t)
        assert len(q.upcoming) == 1

    def test_add_duplicate_ignored(self):
        t = Track(id=1, title="1")
        q = MusicQueue(tracks=[t])
        q.add(t)
        assert len(q.upcoming) == 1

    def test_add_current_not_added(self):
        t = Track(id=1, title="1")
        q = MusicQueue(tracks=[t])
        q.play_next()  # t is now current
        q.add(t)
        assert len(q.upcoming) == 0

    def test_contains_current(self):
        t = Track(id=1, title="1")
        q = MusicQueue(tracks=[t])
        q.play_next()
        assert q.contains(t) is True

    def test_contains_upcoming(self):
        t = Track(id=1, title="1")
        q = MusicQueue(tracks=[t])
        assert q.contains(t) is True

    def test_contains_not_in_queue(self):
        q = MusicQueue()
        assert q.contains(Track(id=99)) is False

    def test_shuffle(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        t3 = Track(id=3, title="3")
        q = MusicQueue(tracks=[t1, t2, t3])
        # Seed for reproducibility
        random.seed(42)
        q.shuffle()
        # With seed 42, the order will be different from original
        assert q.upcoming != [t1, t2, t3]

    def test_toggle_repeat(self):
        q = MusicQueue()
        assert q.repeat == RepeatMode.OFF
        q.toggle_repeat()
        assert q.repeat == RepeatMode.ALL
        q.toggle_repeat()
        assert q.repeat == RepeatMode.ONE
        q.toggle_repeat()
        assert q.repeat == RepeatMode.OFF

    def test_replace_upcoming(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        t3 = Track(id=3, title="3")
        q = MusicQueue(tracks=[t1, t2])
        q.play_next()  # t1 is current
        q.replace_upcoming([t3])
        assert q.upcoming == [t3]

    def test_upcoming_excludes_current(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        q = MusicQueue(tracks=[t1, t2])
        q.play_next()
        assert t1 not in q.upcoming

    def test_is_empty_with_history(self):
        t = Track(id=1, title="1")
        q = MusicQueue(tracks=[t])
        q.play_next()  # t is current, tracks empty, history empty
        assert q.is_empty is False
        q.play_previous()  # t goes back to tracks
        assert q.is_empty is False
        q.play_next()  # t is current again
        assert q.is_empty is False
        # Manually clear everything
        q._tracks = []
        q._history = []
        q._current = None
        assert q.is_empty is True

    def test_play_next_all_repeat_restores_history(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        q = MusicQueue(tracks=[t1, t2], repeat=RepeatMode.ALL)
        q.play_next()  # t1
        q.play_next()  # t2
        q.play_next()  # queue empty, history restored
        assert q.current == t1

    def test_iteration(self):
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        q = MusicQueue(tracks=[t1, t2])
        assert list(q) == [t1, t2]

