"""Event bus and message types for the MusicTUI application."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from textual.message import Message

from model.track import Track

if TYPE_CHECKING:
    from textual.app import App

# ── Type aliases ──────────────────────────────────────────────────────
LikeCallback = Callable[[Track], None]
PlayCallback = Callable[[Track], None]


# ── Playback events ───────────────────────────────────────────────────


class PlaybackStarted(Message):
    """Emitted when a new track starts playing."""

    def __init__(self, track: Track) -> None:
        super().__init__()
        self.track = track


class PlaybackEnded(Message):
    """Emitted when the current track ends."""

    def __init__(self, track: Track) -> None:
        super().__init__()
        self.track = track


class PlaybackStateChanged(Message):
    """Emitted when playback state changes (playing/paused)."""

    def __init__(self, is_playing: bool = False, is_paused: bool = False) -> None:
        super().__init__()
        self.is_playing = is_playing
        self.is_paused = is_paused


class PositionUpdated(Message):
    """Emitted periodically with the current playback position."""

    def __init__(self, position_ms: int = 0, duration_ms: int = 0) -> None:
        super().__init__()
        self.position_ms = position_ms
        self.duration_ms = duration_ms


class QueueUpdated(Message):
    """Emitted when the queue changes."""

    def __init__(self, upcoming: list[Track]) -> None:
        super().__init__()
        self.upcoming = upcoming


# ── Library events ────────────────────────────────────────────────────


class LikedSongsChanged(Message):
    """Emitted when the liked songs collection changes."""


class PlaylistChanged(Message):
    """Emitted when a playlist is created, modified, or deleted."""


# ── Event bus ─────────────────────────────────────────────────────────


class EventBus:
    """Central event bus for decoupled communication between components.

    Components post messages to the app via the event bus, and other
    components subscribe to those messages.  This removes direct
    coupling between the player, UI widgets, and screens.
    """

    def __init__(self, app: App) -> None:
        self._app = app

    def emit(self, message: Message) -> None:
        """Post a message to the app for broadcasting."""
        self._app.post_message(message)

    def emit_playback_started(self, track: Track) -> None:
        self.emit(PlaybackStarted(track))

    def emit_playback_ended(self, track: Track) -> None:
        self.emit(PlaybackEnded(track))

    def emit_playback_state_changed(
        self, is_playing: bool = False, is_paused: bool = False
    ) -> None:
        self.emit(PlaybackStateChanged(is_playing, is_paused))

    def emit_position_updated(self, position_ms: int = 0, duration_ms: int = 0) -> None:
        self.emit(PositionUpdated(position_ms, duration_ms))

    def emit_queue_updated(self, upcoming: list[Track]) -> None:
        self.emit(QueueUpdated(upcoming))

    def emit_liked_songs_changed(self) -> None:
        self.emit(LikedSongsChanged())

    def emit_playlist_changed(self) -> None:
        self.emit(PlaylistChanged())
