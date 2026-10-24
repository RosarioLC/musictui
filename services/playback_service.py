"""Playback service wrapping Player + EventBus."""

from __future__ import annotations

from model.track import Track
from playback.player import Player
from ui.messages import EventBus


class PlaybackService:
    """Service that wraps the Player and exposes event-driven playback.

    Screens and widgets interact with playback through this service
    instead of reaching into ``self.app._player``.
    """

    def __init__(self, player: Player, event_bus: EventBus) -> None:
        self._player = player
        self._event_bus = event_bus

    # ── Public API (delegated to Player) ───────────────────────────────

    @property
    def player(self) -> Player:
        return self._player

    @property
    def current_track(self) -> Track | None:
        return self._player.current_track

    @property
    def upcoming_track(self) -> Track | None:
        return self._player.upcoming_track

    @property
    def is_playing(self) -> bool:
        return self._player.is_playing

    @property
    def is_paused(self) -> bool:
        return self._player.is_paused

    @property
    def position_ms(self) -> int:
        return self._player.position_ms

    @property
    def duration_ms(self) -> int:
        return self._player.duration_ms

    @property
    def volume(self) -> int:
        return self._player.volume

    @property
    def repeat_mode(self) -> str:
        return self._player.repeat_mode

    @property
    def queue(self) -> list[Track]:
        return self._player.queue

    def play(self, track: Track) -> None:
        self._player.play(track)
        self._event_bus.emit_playback_started(track)

    def toggle_play_pause(self) -> None:
        self._player.toggle_play_pause()
        self._event_bus.emit_playback_state_changed(
            is_playing=self._player.is_playing,
            is_paused=self._player.is_paused,
        )

    def play_previous(self) -> None:
        self._player.play_previous()

    def play_next(self) -> None:
        self._player.play_next()

    def seek(self, position_ms: int) -> None:
        self._player.seek(position_ms)

    def set_volume(self, volume: int) -> None:
        self._player.set_volume(volume)

    def set_continuation(self, tracks: list[Track]) -> None:
        self._player.set_continuation(tracks)

    def set_playlist_context(self, value: bool) -> None:
        self._player.set_playlist_context(value)

    def toggle_repeat(self) -> None:
        self._player.toggle_repeat()
