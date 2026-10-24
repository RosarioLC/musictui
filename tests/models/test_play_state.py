"""Tests for the PlayState model."""

from model.play_state import PlayState


class TestPlayState:
    def test_initial(self):
        ps = PlayState()
        assert ps.is_playing is False
        assert ps.is_paused is False

    def test_replace_playing(self):
        ps = PlayState()
        new_ps = ps.replace(is_playing=True)
        assert new_ps.is_playing is True
        assert new_ps.is_paused is False
        assert ps.is_playing is False

    def test_replace_paused(self):
        ps = PlayState()
        new_ps = ps.replace(is_paused=True)
        assert new_ps.is_paused is True
        assert ps.is_paused is False

    def test_replace_both(self):
        ps = PlayState()
        new_ps = ps.replace(is_playing=True, is_paused=True)
        assert new_ps.is_playing is True
        assert new_ps.is_paused is True

    def test_immutability(self):
        ps = PlayState()
        try:
            ps.is_playing = True
            assert False, "Should not mutate frozen dataclass"
        except Exception:
            pass

    def test_replace_preserves_unspecified(self):
        ps = PlayState(is_playing=True, is_paused=False)
        new_ps = ps.replace(is_paused=True)
        assert new_ps.is_playing is True
        assert new_ps.is_paused is True

