"""Tests for the Player with seek, volume, repeat, and track ended."""

from model.repeat_mode import RepeatMode
from model.track import Track
from playback.music_queue import MusicQueue
from playback.player import Player
from tests.playback.fake_backend import FakeBackend


class TestPlayer:
    def test_create(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        assert player.is_playing is False

    def test_play(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        t = Track(id=1, title="Test")
        queue._tracks = [t]
        player.play(t)
        assert player.is_playing is True

    def test_play_adds_to_queue(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        t = Track(id=1, title="Test")
        player.play(t)
        assert player.current_track == t

    def test_toggle_play_pause(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        t = Track(id=1, title="Test")
        queue._tracks = [t]
        player.play(t)
        player.toggle_play_pause()
        assert player.is_paused is True
        player.toggle_play_pause()
        assert player.is_paused is False

    def test_play_previous(self):
        backend = FakeBackend()
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        queue = MusicQueue(tracks=[t1, t2])
        player = Player(backend=backend, queue=queue)
        player.play(t1)
        player.play_previous()
        assert player.current_track == t1

    def test_play_next(self):
        backend = FakeBackend()
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        queue = MusicQueue(tracks=[t1, t2])
        player = Player(backend=backend, queue=queue)
        player.play(t1)
        player.play_next()
        assert player.current_track == t2

    def test_seek(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        player.seek(30000)
        assert backend._position_ms == 30000

    def test_set_volume(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        player.set_volume(50)
        assert backend._volume == 50

    def test_volume_property(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        assert player.volume == 75
        player.set_volume(90)
        assert player.volume == 90

    def test_position_ms(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        player.seek(45000)
        assert player.position_ms == 45000

    def test_duration_ms(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        assert player.duration_ms == 180000

    def test_queue_property(self):
        backend = FakeBackend()
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        queue = MusicQueue(tracks=[t1, t2])
        player = Player(backend=backend, queue=queue)
        queue.play_next()
        assert player.queue == [t2]

    def test_upcoming_track(self):
        backend = FakeBackend()
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        queue = MusicQueue(tracks=[t1, t2])
        player = Player(backend=backend, queue=queue)
        queue.play_next()
        assert player.upcoming_track == t2

    def test_current_track_none_when_empty(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        assert player.current_track is None

    def test_repeat_mode_property(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        assert player.repeat_mode == RepeatMode.OFF

    def test_toggle_repeat(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        player.toggle_repeat()
        assert player.repeat_mode == RepeatMode.ALL
        player.toggle_repeat()
        assert player.repeat_mode == RepeatMode.ONE
        player.toggle_repeat()
        assert player.repeat_mode == RepeatMode.OFF

    def test_set_continuation(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        t1 = Track(id=1, title="1")
        t2 = Track(id=2, title="2")
        player.set_continuation([t1, t2])
        assert player._continuation == [t1, t2]

    def test_set_playlist_context(self):
        backend = FakeBackend()
        queue = MusicQueue()
        player = Player(backend=backend, queue=queue)
        player.set_playlist_context(True)
        assert player._playlist_context is True

    def test_stream_resolver(self):
        backend = FakeBackend()
        queue = MusicQueue()
        calls = []
        def resolver(track):
            calls.append(track.id)
            return f"resolved://{track.id}"
        player = Player(backend=backend, queue=queue, stream_resolver=resolver)
        t = Track(id=1, title="Test", url="original://1")
        queue._tracks = [t]
        player.play(t)
        assert len(calls) == 1
        assert backend._playing is True
