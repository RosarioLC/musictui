"""High-level music playback controller."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from model.repeat_mode import RepeatMode
from model.track import Track
from playback.audio_backend import AudioBackend
from playback.music_queue import MusicQueue

if TYPE_CHECKING:
    from textual.app import App


class Player:
    """High-level playback controller coordinating backend, queue, and UI.

    The :class:`Player` sits between the audio backend, the playback queue,
    and the UI widgets.  It handles track transitions, repeat logic,
    and emits events for UI updates.

    Args:
        backend: The audio playback backend.
        queue: The playback queue manager.
        stream_resolver: Optional callable that resolves a :class:`Track` to
            a playable stream URL.  Falls back to :attr:`~model.track.Track.url`.
    """

    def __init__(
        self,
        backend: AudioBackend,
        queue: MusicQueue,
        stream_resolver: Callable[[Track], str] | None = None,
    ) -> None:
        self._backend: AudioBackend = backend
        self._queue: MusicQueue = queue
        self._stream_resolver: Callable[[Track], str] | None = stream_resolver
        self._app: App | None = None
        self._playlist_context: bool = False
        self._continuation: list[Track] = []

    def set_textual_app(self, app: App) -> None:
        """Register the :class:`~textual.app.App` instance for UI updates."""
        self._app = app

    def play(self, track: Track) -> None:
        """Start playback of *track*.

        If *track* is not already in the queue, it is added first.
        The track is then skipped to and playback begins via the backend.

        Args:
            track: The track to play.
        """
        if not self._queue.contains(track):
            self._queue.add(track)
        self._queue.skip_to(track)
        url = self._stream_resolver(track) if self._stream_resolver else track.url
        self._backend.play(url)

        # Preload assets for the newly playing track.
        app = self._app
        if app is not None:
            preload = getattr(app, "preload_track", None)
            if preload:
                preload(track)

        self._schedule_ui_update()

    def toggle_play_pause(self) -> None:
        """Toggle between playing, paused, and stopped states."""
        if self._backend.is_playing and not self._backend.is_paused:
            self._backend.pause()
        elif self._backend.is_paused:
            self._backend.resume()
        elif self._queue.current:
            self.play(self._queue.current)
        self._schedule_ui_update()

    def play_previous(self) -> None:
        """Play the previous track in the queue."""
        track = self._queue.play_previous()
        if track:
            self.play(track)

    def play_next(self) -> None:
        """Play the next track in the queue."""
        track = self._queue.play_next()
        if track:
            self.play(track)

    def seek(self, position_ms: int) -> None:
        """Seek to *position_ms* within the current track.

        Args:
            position_ms: Target position in milliseconds.
        """
        self._backend.seek(position_ms)
        self._schedule_ui_update()

    def set_volume(self, volume: int) -> None:
        """Set playback volume (0–100).

        Args:
            volume: Volume level.
        """
        self._backend.set_volume(volume)
        self._schedule_ui_update()

    def set_playlist_context(self, active: bool) -> None:
        """Set whether the current session is a playlist context.

        In playlist mode, continuation tracks are cleared so that
        pressing "next" stays within the playlist.

        Args:
            active: ``True`` to enable playlist context.
        """
        self._playlist_context = active
        if active:
            self._continuation.clear()

    def set_continuation(self, tracks: list[Track]) -> None:
        """Set tracks to play after the current playlist ends.

        Args:
            tracks: Tracks to add to the queue when the current playlist finishes.
        """
        self._playlist_context = False
        self._continuation = list(tracks)
        self._queue.replace_upcoming(self._continuation)

    def _on_track_ended(self) -> None:
        """Internal handler called when the backend reports track end.

        Implements repeat logic:

        1. If *ONE* repeat mode: re-play the current track.
        2. Otherwise: advance to the next track, or append continuation
           tracks if the queue is empty and we're not in playlist mode.
        """
        if self._queue.repeat == RepeatMode.ONE:
            current = self._queue.current
            if current is not None:
                self.play(current)
            return

        next_track = self._queue.play_next()

        # If queue is empty and we have continuation tracks, add them.
        if next_track is None and not self._playlist_context and self._continuation:
            for track in self._continuation:
                self._queue.add(track)
            self._continuation.clear()
            next_track = self._queue.play_next()

        if next_track:
            self.play(next_track)

    # Called by the backend when a track ends.
    def on_track_ended(self) -> None:
        """Entry point called by the backend when a track ends."""
        self._on_track_ended()

    def _schedule_ui_update(self) -> None:
        """Schedule a UI update callback via the Textual app, if available."""
        app = self._app
        if app:
            app.call_later(self._update_ui)

    def _update_ui(self) -> None:
        """Refresh mounted playback widgets via the app's event system."""
        app = self._app
        if app is None:
            return
        current = self.current_track
        if current is None:
            return

        # Post events for widgets to consume.
        if hasattr(app, "post_message"):
            from ui.messages import (
                PlaybackStateChanged,
                PositionUpdated,
                QueueUpdated,
            )

            app.post_message(PlaybackStateChanged(self.is_playing, self.is_paused))
            app.post_message(PositionUpdated(self.position_ms, self.duration_ms))
            app.post_message(QueueUpdated(self.queue))

    @property
    def queue(self) -> list[Track]:
        """A snapshot of the upcoming tracks (excludes current)."""
        return list(self._queue.upcoming)

    @property
    def upcoming_track(self) -> Track | None:
        """The track that will play next, or ``None``."""
        return self._queue.upcoming[0] if self._queue.upcoming else None

    @property
    def current_track(self) -> Track | None:
        """The currently playing track, or ``None``."""
        return self._queue.current

    @property
    def is_playing(self) -> bool:
        """``True`` if the backend reports active playback."""
        return self._backend.is_playing

    @property
    def is_paused(self) -> bool:
        """``True`` if playback is paused."""
        return self._backend.is_paused

    @property
    def position_ms(self) -> int:
        """Current playback position in milliseconds."""
        return self._backend.get_position()

    @property
    def duration_ms(self) -> int:
        """Total duration of the current track in milliseconds."""
        return self._backend.get_duration()

    @property
    def volume(self) -> int:
        """Current volume level (0–100)."""
        return self._backend.get_volume()

    @property
    def repeat_mode(self) -> RepeatMode:
        """Current repeat mode."""
        return self._queue.repeat

    def toggle_repeat(self) -> None:
        """Cycle the repeat mode: OFF → ALL → ONE → OFF."""
        self._queue.toggle_repeat()
