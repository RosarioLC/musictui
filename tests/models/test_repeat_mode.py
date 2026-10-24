"""Tests for the RepeatMode enum."""

from model.repeat_mode import RepeatMode


class TestRepeatMode:
    def test_values(self):
        assert RepeatMode.OFF.value == 0
        assert RepeatMode.ALL.value == 1
        assert RepeatMode.ONE.value == 2

    def test_cycle_off_to_all(self):
        assert RepeatMode.OFF.next_mode() == RepeatMode.ALL

    def test_cycle_all_to_one(self):
        assert RepeatMode.ALL.next_mode() == RepeatMode.ONE

    def test_cycle_one_to_off(self):
        assert RepeatMode.ONE.next_mode() == RepeatMode.OFF

    def test_cycle_completes_round(self):
        mode = RepeatMode.OFF
        for expected in [RepeatMode.ALL, RepeatMode.ONE, RepeatMode.OFF]:
            mode = mode.next_mode()
            assert mode == expected

    def test_iteration_three_times(self):
        mode = RepeatMode.OFF
        for _ in range(3):
            mode = mode.next_mode()
        assert mode == RepeatMode.OFF

